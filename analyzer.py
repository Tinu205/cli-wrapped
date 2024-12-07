import os
import sys
import subprocess
from datetime import datetime, timedelta
from collections import defaultdict
import argparse
import shlex
import re

class HistoryAnalyzer:
    def __init__(self, year=None):
        self.year = year or datetime.now().year
        self.command_data = {
            'total_commands': 0,
            'unique_commands': set(),
            'commands_by_month': defaultdict(lambda: {'count': 0, 'commands': defaultdict(int)}),
            'commands_by_weekday': defaultdict(int),
            'commands_by_hour': defaultdict(int),
            'commands_by_day': defaultdict(int),
            'total_command_count': defaultdict(int),
            'first_command': None,
            'first_command_time': datetime.max
        }

    def parse_shell_history(self, shell='bash'):
        """Parse shell history based on shell type"""
        history_files = {
            'bash': os.path.expanduser('~/.bash_history'),
            'zsh': os.path.expanduser('~/.zsh_history'),
            'fish': os.path.expanduser('~/.local/share/fish/fish_history')
        }

        history_file = history_files.get(shell)
        if not history_file or not os.path.exists(history_file):
            raise FileNotFoundError(f"History file not found for {shell}")

        parse_method = getattr(self, f'_parse_{shell}_history')
        return parse_method(history_file)

    def _parse_bash_history(self, history_file):
        with open(history_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    yield line, datetime.now()

    def _parse_zsh_history(self, history_file):
        with open(history_file, 'r') as f:
            for line in f:
                if line.startswith(':'):
                    parts = line.split(';')
                    if len(parts) >= 3:
                        timestamp = datetime.fromtimestamp(int(parts[1]))
                        command = ';'.join(parts[2:]).strip()
                        yield command, timestamp

    def analyze_commands(self, shell='bash'):
        """Analyze commands from shell history"""
        history_data = self.parse_shell_history(shell)

        for command, timestamp in history_data:
            # Skip if not in the specified year
            if timestamp.year != self.year:
                continue

            self._process_command(command, timestamp)

    def _safe_split_command(self, command):
        """Safely split command, handling potential parsing errors"""
        try:
            # First, try standard shlex split
            return shlex.split(command)
        except ValueError:
            # If quotation error, fall back to simple splitting
            # Remove any unclosed quotes
            command = re.sub(r'(\'[^\']*|"[^"]*)', '', command)
            return command.split()

    def _process_command(self, command, timestamp):
        """Process individual command"""
        try:
            # Use safe command splitting method
            cmd_parts = self._safe_split_command(command)
            
            if not cmd_parts:
                return

            base_command = cmd_parts[0]

            # Update command tracking
            self.command_data['total_commands'] += 1
            self.command_data['unique_commands'].add(base_command)
            self.command_data['total_command_count'][base_command] += 1

            # Track first command
            if timestamp < self.command_data['first_command_time']:
                self.command_data['first_command'] = command
                self.command_data['first_command_time'] = timestamp

            # Monthly tracking
            month = timestamp.month
            month_data = self.command_data['commands_by_month'][month]
            month_data['count'] += 1
            month_data['commands'][base_command] += 1

            # Additional tracking
            self.command_data['commands_by_weekday'][timestamp.weekday()] += 1
            self.command_data['commands_by_hour'][timestamp.hour] += 1
            self.command_data['commands_by_day'][timestamp.timetuple().tm_yday] += 1

        except Exception as e:
            # Log or print errors without stopping entire processing
            print(f"Error processing command '{command}': {e}")

    def generate_report(self):
        """Generate a detailed report of command usage"""
        print(f"\n🚀 Command Line Wrapped - {self.year} 🚀\n")
        print(f"Total Commands: {self.command_data['total_commands']}")
        print(f"Unique Commands: {len(self.command_data['unique_commands'])}")

        # Most Used Commands
        print("\n🏆 Most Used Commands:")
        top_commands = sorted(
            self.command_data['total_command_count'].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        for cmd, count in top_commands:
            print(f"{cmd}: {count} times")

        # Most Active Months
        active_months = sorted(
            self.command_data['commands_by_month'].items(), 
            key=lambda x: x[1]['count'], 
            reverse=True
        )[:3]
        
        month_names = [
            'January', 'February', 'March', 'April', 'May', 'June', 
            'July', 'August', 'September', 'October', 'November', 'December'
        ]
        
        print("\n📅 Most Active Months:")
        for month, data in active_months:
            print(f"{month_names[month-1]}: {data['count']} commands")

        # Most Used Commands in Top Months
        print("\n🔝 Top Commands in Most Active Months:")
        for month, data in active_months:
            month_top_commands = sorted(
                data['commands'].items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:3]
            print(f"\n{month_names[month-1]}:")
            for cmd, count in month_top_commands:
                print(f"  {cmd}: {count} times")

        # Most Active Day of Week
        weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        most_active_weekday = max(
            self.command_data['commands_by_weekday'].items(), 
            key=lambda x: x[1]
        )[0]
        print(f"\n🗓️  Most Active Day: {weekdays[most_active_weekday]}")

        # Most Active Hour
        most_active_hour = max(
            self.command_data['commands_by_hour'].items(), 
            key=lambda x: x[1]
        )[0]
        print(f"🕒 Most Active Hour: {most_active_hour}:00")

def main():
    parser = argparse.ArgumentParser(description='Shell Command History Analyzer')
    parser.add_argument('--year', type=int, default=None, help='Year to analyze')
    parser.add_argument('--shell', type=str, default='bash', help='Shell type (bash/zsh/fish)')
    
    args = parser.parse_args()
    
    analyzer = HistoryAnalyzer(args.year)
    analyzer.analyze_commands(args.shell)
    analyzer.generate_report()

if __name__ == '__main__':
    main()
