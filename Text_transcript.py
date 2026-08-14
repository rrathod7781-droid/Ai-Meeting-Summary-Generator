import sys

def transcript():
    print("Enter your transcript (Press Ctrl+D or Ctrl+Z+Enter to finish):")
    transcript = sys.stdin.read()
    return transcript
