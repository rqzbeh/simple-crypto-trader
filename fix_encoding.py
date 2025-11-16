"""Fix encoding issues by removing emoji characters"""
import re

def remove_emojis(text):
    """Remove emoji characters from text"""
    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # emoticons
                               u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                               u"\U0001F680-\U0001F6FF"  # transport & map symbols
                               u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                               u"\U00002702-\U000027B0"
                               u"\U000024C2-\U0001F251"
                               "]+", flags=re.UNICODE)
    return emoji_pattern.sub('', text)

# Read main.py
with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace emojis with text equivalents
replacements = {
    '🚀': '[*]',
    '📰': '[NEWS]',
    '⏰': '[TIME]',
    '💰': '[MODE]',
    '⏱️': '[TIMEFRAME]',
    '🎯': '[TARGET]',
    '📊': '[LEVERAGE]',
    '🎲': '[RR]',
    '🛡️': '[RISK]',
    '🔍': '[CHECK]',
    '⚠️': '[WARNING]',
    '📈': '[ANALYZE]',
    '✅': '[OK]',
    'ℹ️': '[INFO]',
    '❌': '[ERROR]',
    '✓': 'OK',
    '✗': 'NO'
}

for emoji, text in replacements.items():
    content = content.replace(emoji, text)

# Save fixed version
with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed encoding issues in main.py")
