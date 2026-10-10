import pandas as pd
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

rad_data = pd.read_csv('/Users/Selina/Documents/DBMI/data/mimic-iv-note-deidentified-free-text-clinical-notes-2.2/note/radiology.csv')
radd_data = pd.read_csv('/Users/Selina/Documents/DBMI/data/mimic-iv-note-deidentified-free-text-clinical-notes-2.2/note/radiology_detail.csv')
for col in rad_data.columns:
    print(col)

dis_data = pd.read_csv('/Users/Selina/Documents/DBMI/data/mimic-iv-note-deidentified-free-text-clinical-notes-2.2/note/discharge.csv')
disd_data = pd.read_csv('/Users/Selina/Documents/DBMI/data/mimic-iv-note-deidentified-free-text-clinical-notes-2.2/note/radiology_detail.csv')
for col in disd_data.columns:
    print(col)
    