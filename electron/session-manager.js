/**
 * SessionManager - Tracks multiple Claude Code instances
 *
 * Each Claude session has:
 * - id: Unique identifier (terminal_pid + timestamp)
 * - pid: Process ID of the Claude Code instance
 * - context: What Claude is working on (files, tools)
 * - status: 'active' | 'waiting_exercise' | 'exercising' | 'complete'
 * - lastActivity: Timestamp of last activity
 * - createdAt: When the session was registered
 */

const SESSION_TIMEOUT_MS = 10 * 60 * 1000; // 10 minutes

class SessionManager {
  constructor() {
    this.sessions = new Map();

    // Cleanup stale sessions every minute
    this.cleanupInterval = setInterval(() => this.cleanup(), 60 * 1000);
  }

  /**
   * Register a new Claude session
   * @param {string} id - Session identifier
   * @param {object} data - Session data (pid, context, status)
   * @returns {object} The created session
   */
  register(id, data = {}) {
    const session = {
      id,
      pid: data.pid || null,
      context: data.context || {},
      status: data.status || 'active',
      lastActivity: Date.now(),
      createdAt: Date.now(),
      activityLog: []
    };

    this.sessions.set(id, session);
    console.log(`Session registered: ${id}`);
    return session;
  }

  /**
   * Update activity for a session
   * @param {string} id - Session identifier
   * @param {object} activity - Activity data (tool_name, file_path, etc.)
   * @returns {object|null} Updated session or null if not found
   */
  updateActivity(id, activity) {
    const session = this.sessions.get(id);
    if (!session) {
      // Auto-register if session doesn't exist
      return this.register(id, { context: activity });
    }

    session.lastActivity = Date.now();

    // Update context with latest activity
    if (activity.tool_name) {
      session.context.lastTool = activity.tool_name;
    }
    if (activity.file_path) {
      session.context.lastFile = activity.file_path;
      session.context.summary = `Editing ${this.basename(activity.file_path)}`;
    }
    if (activity.context) {
      Object.assign(session.context, activity.context);
    }

    // Keep activity log (last 10 items)
    session.activityLog.push({
      timestamp: Date.now(),
      ...activity
    });
    if (session.activityLog.length > 10) {
      session.activityLog.shift();
    }

    // If we're getting activity, session is active
    if (session.status === 'complete') {
      session.status = 'active';
    }

    console.log(`Session activity: ${id} - ${activity.tool_name || 'update'}`);
    return session;
  }

  /**
   * Mark a session as complete (Claude finished)
   * @param {string} id - Session identifier
   * @returns {object|null} Updated session or null if not found
   */
  markComplete(id) {
    const session = this.sessions.get(id);
    if (session) {
      session.status = 'complete';
      session.lastActivity = Date.now();
      console.log(`Session complete: ${id}`);
    }
    return session;
  }

  /**
   * Set session status to exercising
   * @param {string} id - Session identifier
   */
  markExercising(id) {
    const session = this.sessions.get(id);
    if (session) {
      session.status = 'exercising';
      session.lastActivity = Date.now();
    }
    return session;
  }

  /**
   * Get a session by ID
   * @param {string} id - Session identifier
   * @returns {object|null} Session or null if not found
   */
  get(id) {
    return this.sessions.get(id) || null;
  }

  /**
   * Get all sessions as an array
   * @returns {array} Array of session objects
   */
  getAll() {
    return Array.from(this.sessions.values());
  }

  /**
   * Get active sessions (not complete)
   * @returns {array} Array of active session objects
   */
  getActive() {
    return this.getAll().filter(s => s.status !== 'complete');
  }

  /**
   * Remove a session
   * @param {string} id - Session identifier
   */
  remove(id) {
    this.sessions.delete(id);
    console.log(`Session removed: ${id}`);
  }

  /**
   * Cleanup stale sessions (no activity for SESSION_TIMEOUT_MS)
   */
  cleanup() {
    const now = Date.now();
    const stale = [];

    for (const [id, session] of this.sessions) {
      if (now - session.lastActivity > SESSION_TIMEOUT_MS) {
        stale.push(id);
      }
    }

    for (const id of stale) {
      this.remove(id);
    }

    if (stale.length > 0) {
      console.log(`Cleaned up ${stale.length} stale sessions`);
    }
  }

  /**
   * Get count of sessions by status
   * @returns {object} Counts by status
   */
  getCounts() {
    const counts = { active: 0, exercising: 0, complete: 0, total: 0 };
    for (const session of this.sessions.values()) {
      counts.total++;
      counts[session.status] = (counts[session.status] || 0) + 1;
    }
    return counts;
  }

  /**
   * Helper to get basename of a path
   */
  basename(filePath) {
    if (!filePath) return '';
    return filePath.split(/[\\/]/).pop();
  }

  /**
   * Destroy the session manager
   */
  destroy() {
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval);
    }
    this.sessions.clear();
  }
}

module.exports = SessionManager;
