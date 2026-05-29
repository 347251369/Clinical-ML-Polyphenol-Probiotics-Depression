# preprocess.py
import pandas as pd
from sklearn.model_selection import train_test_split

def main():
    # 直接在代码中定义参数
    input_file = "models/train_filtered_materials.csv"           # 原始输入 CSV 文件
    train_output = "data/train_clean.csv"  # 输出训练集 CSV 文件
    val_output = "data/val_clean.csv"      # 输出验证集 CSV 文件
    val_size = 0.2                    # 验证集比例 (0-1)
    random_state = 42                 # 随机种子

    # 1. 读取原始数据
    df = pd.read_csv(input_file)

    # 2. 剔除没有 CBM 或 VBM 的行
    df_clean = df.dropna(subset=["CBM", "VBM"])
    print(f"原始样本数: {len(df)}, 清洗后样本数: {len(df_clean)}")

    # 3. 划分训练集和验证集
    train_df, val_df = train_test_split(
        df_clean,
        test_size=val_size,
        random_state=random_state
    )

    print(f"训练集样本数: {len(train_df)}, 验证集样本数: {len(val_df)}")

    # 4. 保存到 CSV
    train_df.to_csv(train_output, index=False)
    val_df.to_csv(val_output, index=False)
    print(f"已保存: {train_output}, {val_output}")

if __name__ == "__main__":
    main()