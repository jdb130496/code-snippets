import tabula
import pandas as pd
input_file = 'D:\dgbdata\EMI Finding Implicit Rate Of Interest - Sheet1.pdf'
output_file = 'D:\dgbdata\emi.csv'
#area=[144, 18, 780, 774]
area = [1*72, 0.25*72, 8.10*72, 10.80*72]
dfs = tabula.read_pdf(input_file, pages='all', area=area, pandas_options={'header': None})
df = pd.concat(dfs)
df.to_csv(output_file, index=False, sep='|')
