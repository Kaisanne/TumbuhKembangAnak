# **1. IMPORT LIBRARY**
import pandas as pd

# **2. IMPORT CSV**
path = "./TB-U Male.csv"
df_tbu_m = pd.read_csv(path)

path = "./TB-U Female.csv"
df_tbu_f = pd.read_csv(path)

path = "./BB-U Male.csv"
df_bbu_m = pd.read_csv(path)

path = "./BB-U Female.csv"
df_bbu_f = pd.read_csv(path)

# **3. CONVERT DATA TO Z-SCORE**
# **3.1 Get Row of TB and BB**
def getRowWeight(gender, bulan):
    if(gender == "perempuan"):
        row = df_bbu_f.loc[bulan]
        return row
    elif (gender == "laki-laki"):
        row = df_bbu_m.loc[bulan]
        return row

def getRowHeight(gender, bulan):
    if(gender == "perempuan"):
        row = df_tbu_f.loc[bulan]
        return row
    elif (gender == "laki-laki"):
        row = df_tbu_m.loc[bulan]
        return row

# **3.2 Get Z-Score**
def ZSWeight(gender, bulan, berat):
    bb = getRowWeight(gender, bulan)
    zscore = 0
    if (berat < bb["Median"]):
        zscore = (berat - bb["Median"])/(bb["Median"] - bb["-1 SD"])
    elif (berat > bb["Median"]):
        zscore = (berat - bb["Median"])/(bb["+1 SD"] - bb["Median"])
    else:
        zscore = (berat - bb["Median"])/(bb["Median"])
    return zscore

def ZSHeight(gender, bulan, tinggi):
    tb = getRowHeight(gender, bulan)
    zscore=0
    if (tinggi < tb["Median"]):
        zscore = (tinggi - tb["Median"])/(tb["Median"] - tb["-1 SD"])
    elif (tinggi > tb["Median"]):
        zscore = (tinggi - tb["Median"])/(tb["+1 SD"] - tb["Median"])
    return zscore

# **4. FUZZY LOGIC **
# **4.1 Fuzzifikasi (Menentukan Derajat Keanggotaan)**
# **4.1.1 Tinggi**
def sangat_pendek(x):
    if x <= -4:
        return 1.0
    elif -4 < x < -2.5:
        return (-2.5 - x) / 1.5
    else:
        return 0.0

def pendek(x):
    if -3.5 <= x < -3:
        return (x - (-3.5)) / 0.5
    elif -3 <= x < -2:
        return 1.0
    elif -2 <= x < -1.5:
        return ((-1.5) - x) /  0.5
    else:
        return 0.0

def t_normal(x):
    if -2.5 <= x < -2:
        return (x - (-2.5)) / 0.5
    elif -2 <= x < 3:
        return 1.0
    elif 3 <= x < 3.5:
        return (3.5 - x) / 0.5
    else:
        return 0.0

def tinggi(x):
    if x <= 2.5:
        return 0.0
    elif 2.5 < x < 4:
        return (x - 2.5) / 1.5
    else:
        return 1.0

def t_fuzzify(x):
    return {
        'sangat_pendek': sangat_pendek(x),
        'pendek': pendek(x),
        'normal': t_normal(x),
        'tinggi': tinggi(x)
    }

# **4.1.2 Berat Badan **
def sangat_kurang(x):
    if x <= -4:
        return 1.0
    elif -4 < x < -2.5:
        return (-2.5 - x) / 1.5
    else:
        return 0.0

def kurang(x):
    if -3.5 <= x < -3:
        return (x - (-3.5)) / 0.5
    elif -3 <= x < -2:
        return 1.0
    elif -2 <= x < -1.5:
        return ((-1.5) - x) /  0.5
    else:
        return 0.0

def b_normal(x):
    if -2.5 <= x < -2:
        return (x - (-2.5)) / 0.5
    elif -2 <= x < 1:
        return 1.0
    elif 1 <= x < 1.5:
        return (1.5 - x) / 0.5
    else:
        return 0.0

def berlebih(x):
    if x <= 0.5:
        return 0.0
    elif 0.5 < x < 2:
        return (x - 0.5) / 1.5
    else:
        return 1.0

def b_fuzzify(x):
    return {
        'sangat_kurang': sangat_kurang(x),
        'kurang': kurang(x),
        'normal': b_normal(x),
        'berlebih': berlebih(x)
    }

# **4.2 Rule Evaluation**
def t_rule_evaluation(fuzzy_values):
    return {
        'sangat_pendek': fuzzy_values['sangat_pendek'],
        'pendek': fuzzy_values['pendek'],
        'normal': fuzzy_values['normal'],
        'tinggi': fuzzy_values['tinggi']
    }

def b_rule_evaluation(fuzzy_values):
    return {
        'sangat_kurang': fuzzy_values['sangat_kurang'],
        'kurang': fuzzy_values['kurang'],
        'normal': fuzzy_values['normal'],
        'berlebih': fuzzy_values['berlebih']
    }

# **4.3 Defuzzification**
def t_defuzzify(rules):
    sangat_pendek_value = -3.75
    pendek_value = -2.5
    normal_value = 0.5
    tinggi_value = 3.75

    a = (rules['sangat_pendek'] * sangat_pendek_value + rules['pendek'] * pendek_value + rules['normal'] * normal_value + rules['tinggi'] * tinggi_value)
    b = (rules['sangat_pendek'] + rules['pendek'] + rules['normal'] + rules['tinggi'])
    centroid = (a / b)

    if centroid < -3:
        return 1
    elif -3 <= centroid < -2:
        return 2
    elif -2 <= centroid <= 3:
        return 3
    elif centroid > 3:
        return 4

def b_defuzzify(rules):
    sangat_kurang_value = -3.75
    kurang_value = -2.5
    normal_value = -0.5
    berlebih_value = 1.75

    a = (rules['sangat_kurang'] * sangat_kurang_value + rules['kurang'] * kurang_value + rules['normal'] * normal_value + rules['berlebih'] * berlebih_value)
    b = (rules['sangat_kurang'] + rules['kurang'] + rules['normal'] + rules['berlebih'])
    centroid = (a / b)

    if centroid < -3:
        return 1
    elif -3 <= centroid < -2:
        return 2
    elif -2 <= centroid <= 1:
        return 3
    elif centroid > 1:
        return 4

def fuzzTB(tb):
    fuzzy_values = t_fuzzify(tb)
    rules = t_rule_evaluation(fuzzy_values)
    output_value = t_defuzzify(rules)
    return output_value

def fuzzBB(bb):
    fuzzy_values = b_fuzzify(bb)
    rules = b_rule_evaluation(fuzzy_values)
    output_value = b_defuzzify(rules)
    return output_value


def statusBerat(zscore):
    if zscore < -3:
        return 1
    elif -3 <= zscore < -2:
        return 2
    elif -2 <= zscore <= 1:
        return 3
    elif zscore > 1:
        return 4

def statusTinggi(zscore):
    if zscore < -3:
        return 1
    elif -3 <= zscore < -2:
        return 2
    elif -2 <= zscore <= 3:
        return 3
    elif zscore > 3:
        return 4