const { app, BrowserWindow, Tray, Menu, ipcMain, session, nativeImage, Notification } = require('electron');
const express = require('express');
const path = require('path');
const fs = require('fs');
const { execSync } = require('child_process');
const os = require('os');
const SessionManager = require('./session-manager');

// Set app and process name
app.name = 'VibeReps';
process.title = 'VibeReps';
if (process.platform === 'darwin') {
  app.setName('VibeReps');
}

// Configuration
const HTTP_PORT = 8800;  // Different from webapp's 8765-8774 range
const WINDOW_WIDTH = 400;
const WINDOW_HEIGHT = 600;

// Global references
let tray = null;
let mainWindow = null;
let httpServer = null;
let sessionManager = null;

// Paths
const isDev = !app.isPackaged;
const resourcesPath = isDev ? path.join(__dirname, '..') : process.resourcesPath;
const exerciseUiPath = isDev
  ? path.join(resourcesPath, 'exercise_ui.html')
  : path.join(resourcesPath, 'exercise_ui.html');
const exercisesPath = isDev
  ? path.join(resourcesPath, 'exercises')
  : path.join(resourcesPath, 'exercises');
const mediapipePath = isDev
  ? path.join(__dirname, 'assets', 'mediapipe')
  : path.join(process.resourcesPath, 'app.asar.unpacked', 'assets', 'mediapipe');
const exerciseLogPath = path.join(os.homedir(), '.vibereps', 'exercises.jsonl');

// Get today's date in YYYY-MM-DD format (local timezone)
function getTodayDate() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

// Convert a timestamp to local YYYY-MM-DD date
function timestampToLocalDate(timestamp) {
  // Parse the timestamp and get local date components
  const date = new Date(timestamp);
  if (isNaN(date.getTime())) return null;
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

// Get today's exercise stats from log file
function getTodayExerciseStats() {
  const today = getTodayDate();
  const stats = {};
  let totalReps = 0;

  try {
    if (fs.existsSync(exerciseLogPath)) {
      const lines = fs.readFileSync(exerciseLogPath, 'utf8').trim().split('\n');
      for (const line of lines) {
        try {
          const entry = JSON.parse(line);
          const date = timestampToLocalDate(entry.timestamp);
          if (date === today && entry.reps > 0 && !entry.exercise?.startsWith('_')) {
            const exercise = entry.exercise || 'unknown';
            stats[exercise] = (stats[exercise] || 0) + entry.reps;
            totalReps += entry.reps;
          }
        } catch (e) { /* skip malformed lines */ }
      }
    }
  } catch (err) {
    console.error('Error reading exercise log:', err);
  }

  return { stats, totalReps };
}

// Get today's Claude Code usage via ccusage
function getTodayClaudeStats() {
  try {
    // ccusage expects YYYYMMDD format
    const today = getTodayDate().replace(/-/g, '');
    const result = execSync(`npx ccusage daily --json --since ${today}`, {
      encoding: 'utf8',
      timeout: 10000,
      stdio: ['pipe', 'pipe', 'pipe']
    });
    const data = JSON.parse(result);
    if (data.daily && data.daily.length > 0) {
      const day = data.daily[0];
      return {
        totalTokens: day.totalTokens || 0,
        totalCost: day.totalCost || 0,
        models: day.modelsUsed || []
      };
    }
  } catch (err) {
    console.error('ccusage error:', err.message);
  }
  return null;
}

// Format exercise name for display
function formatExerciseName(name) {
  return name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

// Format token count for display
function formatTokens(tokens) {
  if (tokens >= 1000000) return `${(tokens / 1000000).toFixed(1)}M`;
  if (tokens >= 1000) return `${(tokens / 1000).toFixed(1)}K`;
  return tokens.toString();
}

// Create tray icon
function createTrayIcon() {
  // Use Template image for macOS (black silhouette, adapts to dark/light mode)
  const iconPath = path.join(__dirname, 'assets', 'iconTemplate.png');

  if (fs.existsSync(iconPath)) {
    // Load and resize for menubar (should be ~18-22px for macOS)
    let icon = nativeImage.createFromPath(iconPath);
    // Resize to appropriate menubar size
    icon = icon.resize({ width: 18, height: 18 });
    // Mark as template for macOS dark/light mode adaptation
    icon.setTemplateImage(true);
    return icon;
  }

  // Fallback: create a simple icon programmatically
  console.log('Creating fallback tray icon');
  const size = 18;
  const canvas = Buffer.alloc(size * size * 4);

  // Simple filled square as fallback
  for (let i = 0; i < size * size; i++) {
    const x = i % size;
    const y = Math.floor(i / size);
    // Draw a simple dumbbell shape
    const isWeight = (x < 4 || x >= size - 4) && y >= 4 && y < size - 4;
    const isBar = y >= 7 && y < 11 && x >= 4 && x < size - 4;
    if (isWeight || isBar) {
      canvas[i * 4] = 0;     // R
      canvas[i * 4 + 1] = 0; // G
      canvas[i * 4 + 2] = 0; // B
      canvas[i * 4 + 3] = 255; // A
    }
  }

  const icon = nativeImage.createFromBuffer(canvas, { width: size, height: size });
  icon.setTemplateImage(true);
  return icon;
}

// Setup HTTP API server
function setupHttpServer() {
  const expressApp = express();
  expressApp.use(express.json());

  // CORS headers for local requests
  expressApp.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.header('Access-Control-Allow-Headers', 'Content-Type');
    if (req.method === 'OPTIONS') {
      return res.sendStatus(200);
    }
    next();
  });

  // Serve exercise UI
  expressApp.get('/', (req, res) => {
    res.sendFile(exerciseUiPath);
  });
  expressApp.get('/index.html', (req, res) => {
    res.sendFile(exerciseUiPath);
  });

  // Serve exercise list with full metadata
  expressApp.get('/exercises', (req, res) => {
    try {
      const exercises = [];
      const files = fs.readdirSync(exercisesPath)
        .filter(f => f.endsWith('.json') && !f.startsWith('_'))
        .sort();

      for (const file of files) {
        try {
          const content = JSON.parse(fs.readFileSync(path.join(exercisesPath, file), 'utf8'));
          exercises.push({
            id: content.id || file.replace('.json', ''),
            name: content.name || file.replace('.json', ''),
            description: content.description || '',
            category: content.category || 'general',
            reps: content.reps || { normal: 10, quick: 5 },
            file: file
          });
        } catch (e) {
          console.warn(`Failed to parse exercise ${file}:`, e.message);
        }
      }
      res.json(exercises);
    } catch (err) {
      console.error('Failed to read exercises directory:', err);
      res.json([]);
    }
  });

  expressApp.get('/exercises/:name.json', (req, res) => {
    const filePath = path.join(exercisesPath, `${req.params.name}.json`);
    if (fs.existsSync(filePath)) {
      res.sendFile(filePath);
    } else {
      res.status(404).json({ error: 'Exercise not found' });
    }
  });

  // Serve MediaPipe models locally if bundled
  expressApp.use('/mediapipe', express.static(mediapipePath));

  // API: Register a new Claude session
  expressApp.post('/api/session/register', (req, res) => {
    const { session_id, pid, context } = req.body;
    const sessionData = sessionManager.register(session_id || `session-${Date.now()}`, {
      pid,
      context: context || {},
      status: 'active'
    });

    // Update tray tooltip
    updateTrayTooltip();

    // Notify renderer of new session
    if (mainWindow) {
      mainWindow.webContents.send('sessions-updated', sessionManager.getAll());
    }

    res.json({ success: true, session: sessionData });
  });

  // API: Report activity from a Claude session
  expressApp.post('/api/session/activity', (req, res) => {
    const { session_id, tool_name, file_path, context } = req.body;
    const sessionData = sessionManager.updateActivity(session_id, {
      tool_name,
      file_path,
      context
    });

    if (sessionData) {
      // Notify renderer
      if (mainWindow) {
        mainWindow.webContents.send('session-activity', { session_id, tool_name, file_path });
        mainWindow.webContents.send('sessions-updated', sessionManager.getAll());
      }

      // Show the window on edit/write activity
      if (tool_name && ['Edit', 'Write'].includes(tool_name)) {
        showWindow();
      }

      res.json({ success: true, session: sessionData });
    } else {
      res.status(404).json({ error: 'Session not found' });
    }
  });

  // API: Claude finished notification
  expressApp.post('/api/notify', (req, res) => {
    const { session_id, message, notification_type } = req.body;

    // Mark session as complete
    if (session_id) {
      sessionManager.markComplete(session_id);
    }

    // Update renderer
    if (mainWindow) {
      mainWindow.webContents.send('claude-complete', { session_id, message });
      mainWindow.webContents.send('sessions-updated', sessionManager.getAll());
    }

    // Show desktop notification
    if (Notification.isSupported()) {
      new Notification({
        title: 'Claude Finished',
        body: message || 'Claude has completed the task'
      }).show();
    }

    updateTrayTooltip();
    res.json({ success: true });
  });

  // API: Exercise completed
  expressApp.post('/api/complete', (req, res) => {
    const { session_id, exercise, reps, duration } = req.body;

    // Filter out internal states and zero-rep entries (same as Python hook)
    let logged = false;
    if (exercise && !exercise.startsWith('_') && reps > 0) {
      // Log exercise locally
      const logEntry = {
        timestamp: new Date().toISOString(),
        session_id,
        exercise,
        reps,
        duration
      };
      logExercise(logEntry);
      logged = true;

      // Notify renderer
      if (mainWindow) {
        mainWindow.webContents.send('exercise-complete', logEntry);
      }

      // Refresh menu to show updated stats
      if (tray) {
        tray.setContextMenu(buildContextMenu());
      }
    }

    res.json({ success: true, logged });
  });

  // API: Get status (backward compatibility)
  expressApp.get('/api/status', (req, res) => {
    const sessions = sessionManager.getAll();
    const hasComplete = sessions.some(s => s.status === 'complete');
    res.json({
      active_sessions: sessions.length,
      claude_complete: hasComplete,
      sessions: sessions
    });
  });

  // Legacy endpoints for backward compatibility
  expressApp.get('/status', (req, res) => {
    const sessions = sessionManager.getAll();
    const hasComplete = sessions.some(s => s.status === 'complete');
    res.json({
      claude_complete: hasComplete,
      exercise_complete: false
    });
  });

  expressApp.post('/complete', (req, res) => {
    const { exercise, reps, duration } = req.body;
    // Filter out internal states and zero-rep entries (same as Python hook)
    if (exercise && !exercise.startsWith('_') && reps > 0) {
      logExercise({ timestamp: new Date().toISOString(), exercise, reps, duration });
      // Refresh menu to show updated stats
      if (tray) {
        tray.setContextMenu(buildContextMenu());
      }
    }
    res.json({ success: true });
  });

  expressApp.post('/notify', (req, res) => {
    if (mainWindow) {
      mainWindow.webContents.send('claude-complete', req.body);
    }
    res.json({ success: true });
  });

  expressApp.get('/context', (req, res) => {
    const sessions = sessionManager.getAll();
    if (sessions.length > 0) {
      res.json(sessions[0].context || {});
    } else {
      res.json({});
    }
  });

  expressApp.post('/shutdown', (req, res) => {
    res.json({ success: true });
    // Don't actually shutdown - we're a persistent menubar app
  });

  // Start server
  httpServer = expressApp.listen(HTTP_PORT, 'localhost', () => {
    console.log(`VibeReps HTTP server running on http://localhost:${HTTP_PORT}`);
  });

  httpServer.on('error', (err) => {
    if (err.code === 'EADDRINUSE') {
      console.error(`Port ${HTTP_PORT} is in use. Another instance may be running.`);
    } else {
      console.error('HTTP server error:', err);
    }
  });
}

// Log exercise to local JSONL file
function logExercise(entry) {
  const logDir = path.join(app.getPath('home'), '.vibereps');
  const logFile = path.join(logDir, 'exercises.jsonl');

  try {
    if (!fs.existsSync(logDir)) {
      fs.mkdirSync(logDir, { recursive: true });
    }
    fs.appendFileSync(logFile, JSON.stringify(entry) + '\n');
  } catch (err) {
    console.error('Failed to log exercise:', err);
  }
}

// Update tray tooltip with session count
function updateTrayTooltip() {
  if (!tray) return;

  const sessions = sessionManager.getAll();
  const activeCount = sessions.filter(s => s.status === 'active').length;

  const tooltip = activeCount > 0
    ? `VibeReps - ${activeCount} Claude${activeCount > 1 ? 's' : ''} working`
    : 'VibeReps';
  tray.setToolTip(tooltip);
}

// Show the main window (recreate if destroyed)
function showWindow() {
  if (!mainWindow || mainWindow.isDestroyed()) {
    createWindow();
  }
  if (mainWindow.isMinimized()) mainWindow.restore();
  mainWindow.show();
  mainWindow.focus();
}

// Setup camera permissions
function setupPermissions() {
  session.defaultSession.setPermissionRequestHandler((webContents, permission, callback) => {
    const allowedPermissions = ['media', 'mediaKeySystem'];
    if (allowedPermissions.includes(permission)) {
      callback(true);
    } else {
      callback(false);
    }
  });

  session.defaultSession.setPermissionCheckHandler((webContents, permission) => {
    const allowedPermissions = ['media', 'mediaKeySystem'];
    return allowedPermissions.includes(permission);
  });
}

// Create the main window
function createWindow() {
  mainWindow = new BrowserWindow({
    width: WINDOW_WIDTH,
    height: WINDOW_HEIGHT,
    show: false,  // Start hidden
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      webSecurity: true
    },
    resizable: true,
    movable: true,
    minimizable: true,
    maximizable: false,
    title: 'VibeReps'
  });

  // Load from HTTP server so MediaPipe paths work correctly
  // Load with quick=true to auto-select random exercise
  mainWindow.loadURL(`http://localhost:${HTTP_PORT}/?electron=true&quick=true`);

  mainWindow.on('close', (event) => {
    // Hide instead of close (unless app is quitting)
    if (!app.isQuitting) {
      event.preventDefault();
      mainWindow.hide();
    }
  });

  mainWindow.on('show', () => {
    // Send current sessions to renderer
    mainWindow.webContents.send('sessions-updated', sessionManager.getAll());
    // Inject mediapipe path for local loading
    const mediapipeUrl = `http://localhost:${HTTP_PORT}/mediapipe`;
    mainWindow.webContents.send('mediapipe-path', mediapipeUrl);
  });
}

// Build the context menu with current stats
function buildContextMenu() {
  const menuItems = [];

  // Today's exercise stats
  const { stats: exerciseStats, totalReps } = getTodayExerciseStats();

  menuItems.push({
    label: `💪 Today: ${totalReps} reps`,
    enabled: false
  });

  // Add individual exercise breakdown if any
  const exercises = Object.entries(exerciseStats);
  if (exercises.length > 0) {
    for (const [exercise, reps] of exercises.sort((a, b) => b[1] - a[1]).slice(0, 5)) {
      menuItems.push({
        label: `    ${formatExerciseName(exercise)}: ${reps}`,
        enabled: false
      });
    }
  }

  menuItems.push({ type: 'separator' });

  // Today's Claude Code stats
  const claudeStats = getTodayClaudeStats();
  if (claudeStats) {
    menuItems.push({
      label: `🤖 Claude: ${formatTokens(claudeStats.totalTokens)} tokens ($${claudeStats.totalCost.toFixed(2)})`,
      enabled: false
    });
  } else {
    menuItems.push({
      label: '🤖 Claude: No usage data',
      enabled: false
    });
  }

  menuItems.push({ type: 'separator' });

  // Actions
  menuItems.push({
    label: 'Show VibeReps',
    click: () => showWindow()
  });

  menuItems.push({
    label: 'Refresh Stats',
    click: () => {
      tray.setContextMenu(buildContextMenu());
    }
  });

  menuItems.push({ type: 'separator' });

  menuItems.push({
    label: 'Quit',
    click: () => {
      app.isQuitting = true;
      if (httpServer) httpServer.close();
      app.quit();
    }
  });

  return Menu.buildFromTemplate(menuItems);
}

// Create the tray icon and menu
function createTray() {
  const icon = createTrayIcon();
  tray = new Tray(icon);

  tray.setToolTip('VibeReps');
  tray.setContextMenu(buildContextMenu());

  // Right-click shows context menu (default behavior)
  // Left-click also shows context menu instead of opening window
  tray.on('click', () => {
    tray.popUpContextMenu();
  });

  // Refresh menu periodically (every 5 minutes)
  setInterval(() => {
    if (tray) {
      tray.setContextMenu(buildContextMenu());
    }
  }, 5 * 60 * 1000);

  console.log('VibeReps tray created');
}

// IPC handlers
function setupIPC() {
  ipcMain.handle('get-sessions', () => {
    return sessionManager.getAll();
  });

  ipcMain.handle('get-mediapipe-path', () => {
    return `http://localhost:${HTTP_PORT}/mediapipe`;
  });

  ipcMain.handle('is-electron', () => {
    return true;
  });

  ipcMain.on('exercise-complete', (event, data) => {
    // Filter out internal states and zero-rep entries (same as Python hook)
    if (data.exercise && !data.exercise.startsWith('_') && data.reps > 0) {
      logExercise(data);
    }
  });
}

// App lifecycle
app.whenReady().then(() => {
  // Initialize session manager
  sessionManager = new SessionManager();

  // Setup permissions before creating windows
  setupPermissions();

  // Start HTTP server
  setupHttpServer();

  // Setup IPC handlers
  setupIPC();

  // Create window and tray
  createWindow();
  createTray();

  console.log('VibeReps menubar ready');
});

app.on('window-all-closed', () => {
  // Don't quit on window close - we're a menubar app
});

app.on('before-quit', () => {
  app.isQuitting = true;
  if (httpServer) {
    httpServer.close();
  }
});

// Handle activate (macOS)
app.on('activate', () => {
  showWindow();
});
