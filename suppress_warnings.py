# Suppress Google ADK experimental warnings
import warnings
warnings.filterwarnings('ignore', message='.*EXPERIMENTAL.*')
warnings.filterwarnings('ignore', module='google_adk.*')
warnings.filterwarnings('ignore', module='google_genai.*')
