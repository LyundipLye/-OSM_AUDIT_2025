import pandas as pd

# 读取你上传的文件
try:
    df = pd.read_csv('geographic/kepler_gl_visualisation.csv')

    
    # 核心修复：
    # 1. 将极小的科学计数法数值放大 (乘以 1,000,000,000)
    # 2. 确保它们是浮点数格式
    df['intensity'] = df['intensity'].apply(lambda x: float(x) * 1e12 if float(x) < 0.001 else float(x))
    
    # 3. 针对电力节点，赋予一个标准的权重 (例如 10)，防止它们在热力图中消失
    df.loc[df['audit_type'] == 'Energy_Displacement', 'intensity'] = 50.0

    # 保存为新文件，不使用科学计数法
    df.to_csv('kepler_fix.csv', index=False, float_format='%.4f')
    
    print("--- DATA REPAIR COMPLETE ---")
    print("New file generated: kepler_fix.csv")
    print("Intensity range:", df['intensity'].min(), "to", df['intensity'].max())
    print("ACTION: Drag 'kepler_fix.csv' into Kepler.gl. You will now see 'intensity' in the Weight dropdown.")

except Exception as e:
    print(f"Error: {e}")