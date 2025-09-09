import warnings

# Since some warnings are raised at import time, I found this solution
warnings.filterwarnings("ignore", category=DeprecationWarning)
