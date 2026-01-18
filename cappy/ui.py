"""UI utilities for Cappy Code - colors, progress bars, formatting."""

import sys
from typing import Optional


class Colors:
    """ANSI color codes for terminal output."""
    
    # Basic colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # Styles
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    
    # Reset
    RESET = '\033[0m'
    
    @classmethod
    def strip_colors(cls, text: str) -> str:
        """Remove all ANSI color codes from text."""
        import re
        return re.sub(r'\033\[[0-9;]+m', '', text)


def colorize(text: str, color: str, bold: bool = False) -> str:
    """
    Colorize text with ANSI codes.
    
    Args:
        text: Text to colorize
        color: Color code from Colors class
        bold: Make text bold
    
    Returns:
        Colorized text
    """
    if bold:
        return f"{Colors.BOLD}{color}{text}{Colors.RESET}"
    return f"{color}{text}{Colors.RESET}"


def success(text: str) -> str:
    """Format success message in green."""
    return colorize(f"✓ {text}", Colors.GREEN, bold=True)


def error(text: str) -> str:
    """Format error message in red."""
    return colorize(f"✗ {text}", Colors.RED, bold=True)


def warning(text: str) -> str:
    """Format warning message in yellow."""
    return colorize(f"⚠ {text}", Colors.YELLOW, bold=True)


def info(text: str) -> str:
    """Format info message in blue."""
    return colorize(f"ℹ {text}", Colors.BLUE)


def highlight(text: str) -> str:
    """Highlight text in cyan."""
    return colorize(text, Colors.CYAN, bold=True)


class ProgressBar:
    """Simple progress bar for terminal."""
    
    def __init__(self, total: int, prefix: str = "", width: int = 40):
        """
        Initialize progress bar.
        
        Args:
            total: Total number of items
            prefix: Prefix text
            width: Width of progress bar in characters
        """
        self.total = total
        self.prefix = prefix
        self.width = width
        self.current = 0
    
    def update(self, n: int = 1):
        """
        Update progress by n items.
        
        Args:
            n: Number of items completed
        """
        self.current += n
        self._render()
    
    def _render(self):
        """Render the progress bar."""
        if self.total == 0:
            percent = 100
        else:
            percent = int(100 * self.current / self.total)
        
        filled = int(self.width * self.current / self.total) if self.total > 0 else self.width
        bar = '█' * filled + '░' * (self.width - filled)
        
        sys.stdout.write(f'\r{self.prefix} |{bar}| {percent}% ({self.current}/{self.total})')
        sys.stdout.flush()
        
        if self.current >= self.total:
            sys.stdout.write('\n')
            sys.stdout.flush()
    
    def finish(self):
        """Mark progress as complete."""
        self.current = self.total
        self._render()


class Spinner:
    """Simple spinner for long-running operations."""
    
    FRAMES = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    
    def __init__(self, message: str = "Working..."):
        """
        Initialize spinner.
        
        Args:
            message: Message to display
        """
        self.message = message
        self.frame = 0
        self.running = False
    
    def start(self):
        """Start the spinner."""
        self.running = True
        self._render()
    
    def stop(self, final_message: Optional[str] = None):
        """
        Stop the spinner.
        
        Args:
            final_message: Optional final message to display
        """
        self.running = False
        sys.stdout.write('\r' + ' ' * (len(self.message) + 5) + '\r')
        if final_message:
            sys.stdout.write(final_message + '\n')
        sys.stdout.flush()
    
    def _render(self):
        """Render the spinner frame."""
        if not self.running:
            return
        
        frame = self.FRAMES[self.frame % len(self.FRAMES)]
        sys.stdout.write(f'\r{frame} {self.message}')
        sys.stdout.flush()
        self.frame += 1


def print_table(headers: list, rows: list, align: Optional[list] = None):
    """
    Print a formatted table.
    
    Args:
        headers: List of column headers
        rows: List of row data (list of lists)
        align: List of alignment ('left', 'right', 'center') per column
    """
    if not rows:
        return
    
    # Calculate column widths
    col_widths = [len(str(h)) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))
    
    # Default alignment
    if align is None:
        align = ['left'] * len(headers)
    
    # Print header
    header_row = []
    for i, header in enumerate(headers):
        if align[i] == 'right':
            header_row.append(str(header).rjust(col_widths[i]))
        elif align[i] == 'center':
            header_row.append(str(header).center(col_widths[i]))
        else:
            header_row.append(str(header).ljust(col_widths[i]))
    
    print(colorize(' | '.join(header_row), Colors.BOLD, bold=True))
    print('-' * (sum(col_widths) + 3 * (len(headers) - 1)))
    
    # Print rows
    for row in rows:
        row_cells = []
        for i, cell in enumerate(row):
            if align[i] == 'right':
                row_cells.append(str(cell).rjust(col_widths[i]))
            elif align[i] == 'center':
                row_cells.append(str(cell).center(col_widths[i]))
            else:
                row_cells.append(str(cell).ljust(col_widths[i]))
        print(' | '.join(row_cells))


def print_box(text: str, width: Optional[int] = None, style: str = 'single'):
    """
    Print text in a box.
    
    Args:
        text: Text to display
        width: Box width (None = auto)
        style: Box style ('single', 'double', 'rounded')
    """
    lines = text.split('\n')
    
    if width is None:
        width = max(len(line) for line in lines) + 4
    
    # Box characters
    if style == 'double':
        tl, tr, bl, br = '╔', '╗', '╚', '╝'
        h, v = '═', '║'
    elif style == 'rounded':
        tl, tr, bl, br = '╭', '╮', '╰', '╯'
        h, v = '─', '│'
    else:  # single
        tl, tr, bl, br = '┌', '┐', '└', '┘'
        h, v = '─', '│'
    
    # Print box
    print(tl + h * (width - 2) + tr)
    for line in lines:
        padding = width - len(line) - 4
        print(f"{v} {line}{' ' * padding} {v}")
    print(bl + h * (width - 2) + br)
