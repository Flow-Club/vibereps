/**
 * Preload script - Exposes safe APIs to the renderer process
 *
 * This script runs in a privileged context and bridges the gap between
 * the main process (Node.js) and the renderer process (Chromium).
 */

const { contextBridge, ipcRenderer } = require('electron');

// Expose a safe API to the renderer
contextBridge.exposeInMainWorld('electronAPI', {
  // Identity check
  isElectron: true,

  // Get all sessions
  getSessions: () => ipcRenderer.invoke('get-sessions'),

  // Get MediaPipe local path
  getMediapipePath: () => ipcRenderer.invoke('get-mediapipe-path'),

  // Notify main process of exercise completion
  exerciseComplete: (data) => ipcRenderer.send('exercise-complete', data),

  // Subscribe to session updates
  onSessionsUpdated: (callback) => {
    const handler = (event, sessions) => callback(sessions);
    ipcRenderer.on('sessions-updated', handler);
    return () => ipcRenderer.removeListener('sessions-updated', handler);
  },

  // Subscribe to session activity
  onSessionActivity: (callback) => {
    const handler = (event, activity) => callback(activity);
    ipcRenderer.on('session-activity', handler);
    return () => ipcRenderer.removeListener('session-activity', handler);
  },

  // Subscribe to Claude completion
  onClaudeComplete: (callback) => {
    const handler = (event, data) => callback(data);
    ipcRenderer.on('claude-complete', handler);
    return () => ipcRenderer.removeListener('claude-complete', handler);
  },

  // Subscribe to exercise completion
  onExerciseComplete: (callback) => {
    const handler = (event, data) => callback(data);
    ipcRenderer.on('exercise-complete', handler);
    return () => ipcRenderer.removeListener('exercise-complete', handler);
  },

  // Get mediapipe path notification
  onMediapipePath: (callback) => {
    const handler = (event, path) => callback(path);
    ipcRenderer.on('mediapipe-path', handler);
    return () => ipcRenderer.removeListener('mediapipe-path', handler);
  }
});

// Log that preload script ran
console.log('VibeReps preload script loaded');
