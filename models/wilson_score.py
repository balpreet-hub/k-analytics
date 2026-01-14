import math
import scipy.stats as st # Ici "st" veut dire Statistics, pas Streamlit !

def calculate_wilson_lower_bound(row, confidence=0.95):
    n = row['Games']
    if n == 0: return 0
    p = row['Winrate']
    z = st.norm.ppf(1 - (1 - confidence) / 2)
    numerator = p + z**2 / (2 * n) - z * math.sqrt((p * (1 - p) + z**2 / (4 * n)) / n)
    denominator = 1 + z**2 / n
    return numerator / denominator