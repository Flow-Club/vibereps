#!/usr/bin/env python3
"""
MCP server for exercise tracking data and configuration
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    Resource,
    GetPromptResult,
    PromptMessage,
    INVALID_PARAMS,
    INTERNAL_ERROR
)

class ExerciseTrackerMCP:
    def __init__(self):
        self.server = Server("exercise-tracker")
        self.data_file = Path.home() / ".claude_exercise_data.json"
        self.exercise_data = self.load_data()

        # Register MCP endpoints
        self.setup_handlers()

    def load_data(self) -> Dict:
        """Load exercise history from file"""
        if self.data_file.exists():
            try:
                with open(self.data_file) as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading data: {e}")

        return {
            "history": [],
            "goals": {
                "daily_squats": 30,
                "daily_pushups": 30,
                "daily_jumping_jacks": 60
            },
            "streaks": {},
            "total_reps": {
                "squats": 0,
                "pushups": 0,
                "jumping_jacks": 0
            }
        }

    def save_data(self):
        """Persist exercise data"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.exercise_data, f, indent=2)
        except Exception as e:
            print(f"Error saving data: {e}")

    def setup_handlers(self):
        """Register MCP handlers"""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available exercise tracking tools"""
            return [
                Tool(
                    name="log_exercise_session",
                    description="Log a completed exercise session",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "exercise_type": {
                                "type": "string",
                                "enum": ["squats", "pushups", "jumping_jacks"],
                                "description": "Type of exercise performed"
                            },
                            "reps_completed": {
                                "type": "integer",
                                "description": "Number of repetitions completed"
                            },
                            "duration_seconds": {
                                "type": "integer",
                                "description": "Duration of exercise session in seconds"
                            }
                        },
                        "required": ["exercise_type", "reps_completed", "duration_seconds"]
                    }
                ),
                Tool(
                    name="get_exercise_stats",
                    description="Get exercise statistics for a timeframe",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "timeframe": {
                                "type": "string",
                                "enum": ["day", "week", "month", "all"],
                                "description": "Timeframe for statistics",
                                "default": "week"
                            }
                        }
                    }
                ),
                Tool(
                    name="suggest_exercise",
                    description="Suggest an exercise based on context and history",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "context": {
                                "type": "string",
                                "description": "Context for suggestion (e.g., 'break', 'warmup', 'cooldown')",
                                "default": "break"
                            }
                        }
                    }
                ),
                Tool(
                    name="update_goals",
                    description="Update daily exercise goals",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "exercise": {
                                "type": "string",
                                "enum": ["squats", "pushups", "jumping_jacks"],
                                "description": "Exercise type to update goal for"
                            },
                            "daily_target": {
                                "type": "integer",
                                "description": "New daily target reps",
                                "minimum": 1
                            }
                        },
                        "required": ["exercise", "daily_target"]
                    }
                ),
                Tool(
                    name="check_streak",
                    description="Check current exercise streak and motivation",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="get_progress_today",
                    description="Get today's exercise progress toward goals",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent]:
            """Handle tool calls"""
            try:
                if name == "log_exercise_session":
                    return await self.log_exercise_session(
                        arguments["exercise_type"],
                        arguments["reps_completed"],
                        arguments["duration_seconds"]
                    )
                elif name == "get_exercise_stats":
                    return await self.get_exercise_stats(
                        arguments.get("timeframe", "week")
                    )
                elif name == "suggest_exercise":
                    return await self.suggest_exercise(
                        arguments.get("context", "break")
                    )
                elif name == "update_goals":
                    return await self.update_goals(
                        arguments["exercise"],
                        arguments["daily_target"]
                    )
                elif name == "check_streak":
                    return await self.check_streak()
                elif name == "get_progress_today":
                    return await self.get_progress_today()
                else:
                    raise ValueError(f"Unknown tool: {name}")

            except KeyError as e:
                raise ValueError(f"Missing required argument: {e}")
            except Exception as e:
                raise RuntimeError(f"Tool execution error: {e}")

        @self.server.list_resources()
        async def list_resources() -> list[Resource]:
            """List available resources"""
            return [
                Resource(
                    uri="exercise://stats/summary",
                    name="Exercise Statistics Summary",
                    description="Overall exercise statistics and total reps",
                    mimeType="application/json"
                ),
                Resource(
                    uri="exercise://history/recent",
                    name="Recent Exercise History",
                    description="Last 20 exercise sessions",
                    mimeType="application/json"
                ),
                Resource(
                    uri="exercise://goals/current",
                    name="Current Exercise Goals",
                    description="Current daily exercise goals",
                    mimeType="application/json"
                )
            ]

        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """Read a resource by URI"""
            if uri == "exercise://stats/summary":
                return json.dumps(self.exercise_data["total_reps"], indent=2)
            elif uri == "exercise://history/recent":
                recent = self.exercise_data["history"][-20:]
                return json.dumps(recent, indent=2)
            elif uri == "exercise://goals/current":
                return json.dumps(self.exercise_data["goals"], indent=2)
            else:
                raise ValueError(f"Unknown resource: {uri}")

    # Tool implementations
    async def log_exercise_session(
        self,
        exercise_type: str,
        reps_completed: int,
        duration_seconds: int
    ) -> list[TextContent]:
        """Log a completed exercise session"""
        session = {
            "timestamp": datetime.now().isoformat(),
            "exercise": exercise_type,
            "reps": reps_completed,
            "duration": duration_seconds
        }

        self.exercise_data["history"].append(session)
        self.exercise_data["total_reps"][exercise_type] += reps_completed
        self.save_data()

        message = f"✅ Logged {reps_completed} {exercise_type}! Total: {self.exercise_data['total_reps'][exercise_type]}"

        return [TextContent(type="text", text=message)]

    async def get_exercise_stats(self, timeframe: str = "week") -> list[TextContent]:
        """Get exercise statistics for a timeframe"""
        now = datetime.now()

        # Calculate time boundary
        if timeframe == "day":
            boundary = now - timedelta(days=1)
        elif timeframe == "week":
            boundary = now - timedelta(weeks=1)
        elif timeframe == "month":
            boundary = now - timedelta(days=30)
        else:  # all
            boundary = datetime.min

        # Filter sessions by timeframe
        filtered_sessions = [
            s for s in self.exercise_data["history"]
            if datetime.fromisoformat(s["timestamp"]) >= boundary
        ]

        # Calculate stats
        reps_by_exercise = {
            "squats": 0,
            "pushups": 0,
            "jumping_jacks": 0
        }

        for session in filtered_sessions:
            exercise = session["exercise"]
            if exercise in reps_by_exercise:
                reps_by_exercise[exercise] += session["reps"]

        stats = {
            "timeframe": timeframe,
            "total_sessions": len(filtered_sessions),
            "reps_by_exercise": reps_by_exercise,
            "recent_sessions": filtered_sessions[-5:] if filtered_sessions else []
        }

        return [TextContent(type="text", text=json.dumps(stats, indent=2))]

    async def suggest_exercise(self, context: str = "break") -> list[TextContent]:
        """Suggest an exercise based on context and history"""
        # Analyze recent history to suggest variety
        recent = self.exercise_data["history"][-5:] if self.exercise_data["history"] else []
        recent_exercises = [s["exercise"] for s in recent]

        # Suggest the least recent exercise for variety
        exercises = ["squats", "pushups", "jumping_jacks"]
        suggestion = min(exercises, key=lambda x: recent_exercises.count(x))

        # Adjust reps based on performance
        avg_reps = self.calculate_average_reps(suggestion)
        recommended_reps = self.adjust_difficulty(avg_reps)

        result = {
            "exercise": suggestion,
            "recommended_reps": recommended_reps,
            "reason": f"You haven't done {suggestion} recently. Mix it up for balanced fitness!"
        }

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    async def update_goals(self, exercise: str, daily_target: int) -> list[TextContent]:
        """Update daily exercise goals"""
        self.exercise_data["goals"][f"daily_{exercise}"] = daily_target
        self.save_data()

        message = f"Updated {exercise} goal to {daily_target} reps/day"
        return [TextContent(type="text", text=message)]

    async def check_streak(self) -> list[TextContent]:
        """Check current exercise streak"""
        today = datetime.now().date().isoformat()

        # Check if exercised today
        today_sessions = [
            s for s in self.exercise_data["history"]
            if s["timestamp"].startswith(today)
        ]

        current_streak = self.calculate_streak()
        motivation = self.get_motivation_message(current_streak)

        streak_info = {
            "exercised_today": len(today_sessions) > 0,
            "sessions_today": len(today_sessions),
            "current_streak_days": current_streak,
            "motivation": motivation
        }

        return [TextContent(type="text", text=json.dumps(streak_info, indent=2))]

    async def get_progress_today(self) -> list[TextContent]:
        """Get today's exercise progress toward goals"""
        today = datetime.now().date().isoformat()

        # Get today's sessions
        today_sessions = [
            s for s in self.exercise_data["history"]
            if s["timestamp"].startswith(today)
        ]

        # Calculate progress
        progress = {
            "squats": 0,
            "pushups": 0,
            "jumping_jacks": 0
        }

        for session in today_sessions:
            exercise = session["exercise"]
            if exercise in progress:
                progress[exercise] += session["reps"]

        # Compare to goals
        result = {
            "date": today,
            "progress": {}
        }

        for exercise in ["squats", "pushups", "jumping_jacks"]:
            goal = self.exercise_data["goals"].get(f"daily_{exercise}", 0)
            completed = progress[exercise]
            percentage = (completed / goal * 100) if goal > 0 else 0

            result["progress"][exercise] = {
                "completed": completed,
                "goal": goal,
                "percentage": round(percentage, 1),
                "remaining": max(0, goal - completed)
            }

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    # Helper methods
    def calculate_average_reps(self, exercise: str) -> int:
        """Calculate average reps for an exercise"""
        sessions = [
            s["reps"] for s in self.exercise_data["history"]
            if s["exercise"] == exercise
        ]
        return int(sum(sessions) / len(sessions)) if sessions else 10

    def adjust_difficulty(self, current_avg: int) -> int:
        """Progressively increase difficulty"""
        if current_avg < 10:
            return 10
        elif current_avg < 20:
            return current_avg + 2
        else:
            return min(current_avg + 1, 50)  # Cap at 50

    def calculate_streak(self) -> int:
        """Calculate current day streak"""
        if not self.exercise_data["history"]:
            return 0

        streak = 0
        current_date = datetime.now().date()

        for i in range(365):  # Check last year max
            check_date = (current_date - timedelta(days=i)).isoformat()
            day_sessions = [
                s for s in self.exercise_data["history"]
                if s["timestamp"].startswith(check_date)
            ]
            if day_sessions:
                streak += 1
            else:
                break

        return streak

    def get_motivation_message(self, streak: int) -> str:
        """Generate motivational message based on performance"""
        if streak == 0:
            return "Time to start a new streak! You've got this! 💪"
        elif streak < 3:
            return f"Great start! {streak} day streak going!"
        elif streak < 7:
            return f"Awesome! {streak} days strong! Keep it up!"
        elif streak < 30:
            return f"Incredible! {streak} day streak! You're crushing it!"
        else:
            return f"LEGENDARY! {streak} days! You're unstoppable! 🔥"

async def main():
    """Run the MCP server"""
    tracker = ExerciseTrackerMCP()

    async with stdio_server() as (read_stream, write_stream):
        await tracker.server.run(
            read_stream,
            write_stream,
            tracker.server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
