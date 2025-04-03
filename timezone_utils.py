from datetime import datetime
import pytz

def get_ecuador_time():
    """
    Returns the current time in Ecuador's timezone (America/Guayaquil)
    """
    # Get current UTC time
    utc_now = datetime.now(pytz.UTC)
    
    # Convert to Ecuador timezone
    ecuador_tz = pytz.timezone('America/Guayaquil')
    ecuador_time = utc_now.astimezone(ecuador_tz)
    
    return ecuador_time

def format_ecuador_time(timestamp, include_seconds=True):
    """
    Formats a timestamp to Ecuador's timezone and returns a formatted string
    
    Args:
        timestamp: A datetime object or ISO format string
        include_seconds: Whether to include seconds in the formatted time
    
    Returns:
        A formatted string in the format: DD/MM/YYYY HH:MM:SS or DD/MM/YYYY HH:MM
    """
    if isinstance(timestamp, str):
        # Try to parse the ISO format string
        try:
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            # If parsing fails, try to parse as UTC timestamp
            timestamp = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%f')
            timestamp = pytz.UTC.localize(timestamp)
    
    # If the timestamp doesn't have timezone info, assume it's UTC
    if timestamp.tzinfo is None:
        timestamp = pytz.UTC.localize(timestamp)
    
    # Convert to Ecuador timezone
    ecuador_tz = pytz.timezone('America/Guayaquil')
    ecuador_time = timestamp.astimezone(ecuador_tz)
    
    # Format the timestamp
    if include_seconds:
        return ecuador_time.strftime('%d/%m/%Y %H:%M:%S')
    else:
        return ecuador_time.strftime('%d/%m/%Y %H:%M')

