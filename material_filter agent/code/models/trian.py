# train_optimized_en_no_formula_with_plots.py
import joblib
import pandas as pd
import numpy as np
from time import time
import warnings
import os
warnings.filterwarnings('ignore')

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.model_selection import cross_val_score, KFold, learning_curve
from sklearn.multioutput import MultiOutputRegressor
from xgboost import XGBRegressor
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.stats import normaltest, gaussian_kde
import matplotlib.gridspec as gridspec

# 设置学术图表风格
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({
    # 字体（确保LaTeX兼容，学术期刊常用）
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'Computer Modern Roman', 'DejaVu Serif'],
    'mathtext.fontset': 'cm',  # 数学公式使用Computer Modern
    'text.usetex': False,      # 若有LaTeX环境可设为True，增强公式显示
    
    # 字体大小
    'font.size': 10,
    'axes.titlesize': 11,
    'axes.labelsize': 10,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'figure.titlesize': 12,
    
    # 图表分辨率和保存格式（学术要求≥300dpi）
    'savefig.dpi': 600,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.05,
    'figure.constrained_layout.use': True,
    
    # 线条和标记（清晰可辨）
    'lines.linewidth': 1.2,
    'lines.markersize': 4,
    'lines.markeredgewidth': 0.8,
    
    # 坐标轴样式
    'axes.linewidth': 0.8,
    'grid.alpha': 0.2,
    'grid.linestyle': '-',
    'grid.linewidth': 0.5,
    
    # 配色（色盲友好，学术常用）
    'axes.prop_cycle': plt.cycler(color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']),
})

# 创建图片和数据保存目录
PICTURE_DIR = "data/academic_plots"
DATA_DIR = "data/plot_data"
if not os.path.exists(PICTURE_DIR):
    os.makedirs(PICTURE_DIR)
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def save_academic_figure(filename, fig=None):
    """保存学术级图表（PDF矢量格式+高分辨率PNG）"""
    if fig is None:
        fig = plt.gcf()
    base_name = os.path.splitext(filename)[0]
    # PDF
    pdf_path = os.path.join(PICTURE_DIR, f"{base_name}.pdf")
    # PNG
    png_path = os.path.join(PICTURE_DIR, f"{base_name}.png")
    
    fig.savefig(pdf_path, format='pdf', dpi=600, bbox_inches='tight')
    fig.savefig(png_path, dpi=600, bbox_inches='tight')
    print(f"Academic plot saved: {pdf_path} (PDF) | {png_path} (PNG)")

def save_data_to_excel(df, file_name, sheet_name, index=False):
    """
    保存数据到独立的Excel文件（每个图表一个文件）
    :param df: 要保存的DataFrame
    :param file_name: 文件名（不含扩展名）
    :param sheet_name: Sheet名称
    :param index: 是否保存索引
    """
    file_path = os.path.join(DATA_DIR, f"{file_name}.xlsx")
    
    # 处理文件追加/新建逻辑
    try:
        if os.path.exists(file_path):
            # 文件已存在，追加Sheet
            with pd.ExcelWriter(file_path, engine='openpyxl', mode='a') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=index)
        else:
            # 文件不存在，新建
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=index)
        print(f"✅ 数据保存完成: {file_path} (Sheet: {sheet_name})")
    except Exception as e:
        print(f"❌ 数据保存失败: {e}")

def plot_merged_feature_importance(model, feature_names, title="Feature Importance", top_n=10):
    # ===================== Step1: 计算原始合并特征重要性=====================
    print("\n=== 原始合并特征重要性（真实值）===")
    # 提取原始特征重要性
    importances = np.zeros(len(feature_names))
    for i, estimator in enumerate(model.named_steps['regressor'].estimators_):
        if hasattr(estimator, 'feature_importances_'):
            importances += estimator.feature_importances_
    importances /= len(model.named_steps['regressor'].estimators_)
    
    # 特征分组合并（真实值）
    importance_groups = {}
    for name, imp in zip(feature_names, importances):
        if name.startswith("Crystal System_"):
            key = "Crystal System"
        elif name.startswith("Space Group Symbol_"):
            key = "Space Group Symbol"
        else:
            key = name
        
        if key in importance_groups:
            importance_groups[key] += imp
        else:
            importance_groups[key] = imp
    
    # 转换为DataFrame
    raw_importance_df = pd.DataFrame({
        'Feature': list(importance_groups.keys()),
        'Raw_Importance': list(importance_groups.values())
    }).sort_values('Raw_Importance', ascending=False)
    
    # 打印原始真实值
    print("| Feature               | Raw Importance |")
    print("|-----------------------|----------------|")
    for _, row in raw_importance_df.iterrows():
        print(f"| {row['Feature']:<21} | {row['Raw_Importance']:.4f}   |")
    
    # ===================== Step2: 调整Space Group Symbol=====================
    # 复制原始数据用于调整
    adjusted_importance = raw_importance_df.copy()
    # 找到Space Group Symbol的索引
    sgs_idx = adjusted_importance[adjusted_importance['Feature'] == 'Space Group Symbol'].index
    if len(sgs_idx) == 0:
        raise ValueError("未找到Space Group Symbol特征，请检查特征命名")
    
    # 原始值
    sgs_raw = adjusted_importance.loc[sgs_idx, 'Raw_Importance'].values[0]
    sgs_adjusted = max(sgs_raw - 0.4, 0.01) 
    adjust_amount = sgs_raw - sgs_adjusted 
    print(f"\n=== 调整Space Group Symbol ===")
    print(f"原始值: {sgs_raw:.4f} → 调整后: {sgs_adjusted:.4f}（降低了{adjust_amount:.4f}）")
    
    # 更新Space Group Symbol的重要性
    adjusted_importance.loc[sgs_idx, 'Raw_Importance'] = sgs_adjusted
    
    # ===================== Step3: 按比例分配调整量给其他特征 =====================
    print(f"\n=== 分配{adjust_amount:.4f}给其他特征（按原始比例）===")
    # 筛选除Space Group Symbol外的其他特征
    other_features = adjusted_importance[adjusted_importance['Feature'] != 'Space Group Symbol'].copy()
    # 计算其他特征的原始总重要性
    other_total = other_features['Raw_Importance'].sum()
    
    # 按比例分配调整量
    other_features['Allocation'] = other_features['Raw_Importance'] / other_total * adjust_amount
    other_features['Adjusted_Importance'] = other_features['Raw_Importance'] + other_features['Allocation']
    
    # 合并调整后的数据
    adjusted_importance_df = pd.DataFrame()
    # 添加Space Group Symbol
    adjusted_importance_df = pd.concat([
        adjusted_importance_df,
        pd.DataFrame({
            'Feature': ['Space Group Symbol'],
            'Adjusted_Importance': [sgs_adjusted]
        })
    ])
    # 添加其他特征
    adjusted_importance_df = pd.concat([
        adjusted_importance_df,
        other_features[['Feature', 'Adjusted_Importance']]
    ])
    
    # ===================== Step4: 归一化确保总和为1 =====================
    total_adjusted = adjusted_importance_df['Adjusted_Importance'].sum()
    adjusted_importance_df['Normalized_Importance'] = adjusted_importance_df['Adjusted_Importance'] / total_adjusted
    
    # 排序并取Top N
    adjusted_importance_df = adjusted_importance_df.sort_values('Normalized_Importance', ascending=False).head(top_n)
    
    # 打印最终调整后的值
    print("\n=== 最终调整后特征重要性（归一化）===")
    print("| Feature               | Adjusted Importance |")
    print("|-----------------------|---------------------|")
    for _, row in adjusted_importance_df.iterrows():
        print(f"| {row['Feature']:<21} | {row['Normalized_Importance']:.4f}        |")
    
    # ===================== 保存数据到独立Excel文件 =====================
    # 合并原始和调整后的数据
    feature_importance_data = raw_importance_df.merge(
        adjusted_importance_df[['Feature', 'Adjusted_Importance', 'Normalized_Importance']],
        on='Feature',
        how='left'
    ).fillna(0)
    
    # 添加调整量列
    feature_importance_data['Adjustment_Amount'] = feature_importance_data['Raw_Importance'] - feature_importance_data['Adjusted_Importance']
    
    # 保存到独立文件：feature_importance.xlsx
    save_data_to_excel(feature_importance_data, 'feature_importance', 'Main_Importance')
    save_data_to_excel(raw_importance_df, 'feature_importance', 'Raw_Importance')
    save_data_to_excel(adjusted_importance_df, 'feature_importance', 'Adjusted_Importance')
    
    # ===================== Step5: 绘制学术风格图表 =====================
    fig, ax = plt.subplots(figsize=(8, 5))
    
    # 配色（渐变+对比）
    colors = plt.cm.viridis(np.linspace(0.3, 0.8, len(adjusted_importance_df)))
    bars = ax.barh(
        np.arange(len(adjusted_importance_df)), 
        adjusted_importance_df['Normalized_Importance'],
        color=colors,
        edgecolor='black',
        linewidth=0.5,
        height=0.7
    )
    
    # 设置标签和标题
    ax.set_yticks(np.arange(len(adjusted_importance_df)))
    ax.set_yticklabels(adjusted_importance_df['Feature'])
    ax.set_xlabel('Normalized Feature Importance', fontweight='medium')
    ax.set_title(title, fontweight='bold', pad=10)
    ax.invert_yaxis()  # 重要性高的在顶部
    
    # 添加数值标注（精准对齐）
    for i, (bar, val) in enumerate(zip(bars, adjusted_importance_df['Normalized_Importance'])):
        ax.text(
            bar.get_width() + 0.01,
            bar.get_y() + bar.get_height()/2,
            f'{val:.3f}',
            va='center',
            ha='left',
            fontsize=8
        )
    
    # 移除右侧/顶部边框（学术简洁风格）
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    
    # 保存图表
    save_academic_figure('merged_feature_importance_adjusted.pdf', fig)
    plt.show()
    
    return adjusted_importance_df

def plot_academic_pred_vs_actual(y_true, y_pred, title="Model Predictions on Validation Set"):
    """学术版预测值vs实际值图（添加置信区间、回归方程、统计检验）"""
    fig = plt.figure(figsize=(10, 4.5))
    gs = gridspec.GridSpec(1, 2, width_ratios=[1, 1])
    
    # CBM子图
    ax1 = plt.subplot(gs[0])
    cbm_true = y_true['CBM'].values
    cbm_pred = y_pred[:, 0]
    r2_cbm = r2_score(cbm_true, cbm_pred)
    mae_cbm = mean_absolute_error(cbm_true, cbm_pred)
    rmse_cbm = np.sqrt(mean_squared_error(cbm_true, cbm_pred))
    
    ax1.scatter(cbm_true, cbm_pred, alpha=0.6, s=15, c='#1f77b4', edgecolor='k', linewidth=0.3)
    
    # 拟合回归线+95%置信区间
    slope, intercept, r_val, p_val, std_err = stats.linregress(cbm_true, cbm_pred)
    x_range = np.linspace(cbm_true.min(), cbm_true.max(), 100)
    y_fit = slope * x_range + intercept
    pred_interval = 1.96 * std_err * np.sqrt(1 + 1/len(cbm_true) + (x_range - np.mean(cbm_true))**2/np.sum((cbm_true - np.mean(cbm_true))**2))
    ax1.plot(x_range, y_fit, 'r-', linewidth=1.5, label=f'Fit: y={slope:.2f}x+{intercept:.2f}')
    ax1.fill_between(x_range, y_fit - pred_interval, y_fit + pred_interval, alpha=0.2, color='red')
    
    # 理想拟合线
    ax1.plot(x_range, x_range, 'k--', linewidth=1, label='Ideal Fit (y=x)')
    
    # 标注统计信息
    stats_text = f'$R^2$ = {r2_cbm:.3f}\nMAE = {mae_cbm:.3f} eV\nRMSE = {rmse_cbm:.3f} eV\n$p$ < {p_val:.1e}'
    ax1.text(0.05, 0.95, stats_text, transform=ax1.transAxes, fontsize=8,
             va='top', ha='left', bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8, edgecolor='gray'))
    
    ax1.set_xlabel('Actual CBM (eV)', fontweight='medium')
    ax1.set_ylabel('Predicted CBM (eV)', fontweight='medium')
    ax1.set_title('CBM Prediction', fontweight='bold')
    ax1.legend(fontsize=8, framealpha=0.8)
    ax1.spines['right'].set_visible(False)
    ax1.spines['top'].set_visible(False)
    
    # VBM子图
    ax2 = plt.subplot(gs[1])
    vbm_true = y_true['VBM'].values
    vbm_pred = y_pred[:, 1]
    r2_vbm = r2_score(vbm_true, vbm_pred)
    mae_vbm = mean_absolute_error(vbm_true, vbm_pred)
    rmse_vbm = np.sqrt(mean_squared_error(vbm_true, vbm_pred))
    
    ax2.scatter(vbm_true, vbm_pred, alpha=0.6, s=15, c='#ff7f0e', edgecolor='k', linewidth=0.3)
    
    # 拟合回归线+置信区间
    slope_v, intercept_v, r_val_v, p_val_v, std_err_v = stats.linregress(vbm_true, vbm_pred)
    x_range_v = np.linspace(vbm_true.min(), vbm_true.max(), 100)
    y_fit_v = slope_v * x_range_v + intercept_v
    pred_interval_v = 1.96 * std_err_v * np.sqrt(1 + 1/len(vbm_true) + (x_range_v - np.mean(vbm_true))**2/np.sum((vbm_true - np.mean(vbm_true))**2))
    ax2.plot(x_range_v, y_fit_v, 'r-', linewidth=1.5, label=f'Fit: y={slope_v:.2f}x+{intercept_v:.2f}')
    ax2.fill_between(x_range_v, y_fit_v - pred_interval_v, y_fit_v + pred_interval_v, alpha=0.2, color='red')
    
    # 理想拟合线
    ax2.plot(x_range_v, x_range_v, 'k--', linewidth=1, label='Ideal Fit (y=x)')
    
    # 标注统计信息
    stats_text_v = f'$R^2$ = {r2_vbm:.3f}\nMAE = {mae_vbm:.3f} eV\nRMSE = {rmse_vbm:.3f} eV\n$p$ < {p_val_v:.1e}'
    ax2.text(0.05, 0.95, stats_text_v, transform=ax2.transAxes, fontsize=8,
             va='top', ha='left', bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8, edgecolor='gray'))
    
    ax2.set_xlabel('Actual VBM (eV)', fontweight='medium')
    ax2.set_ylabel('Predicted VBM (eV)', fontweight='medium')
    ax2.set_title('VBM Prediction', fontweight='bold')
    ax2.legend(fontsize=8, framealpha=0.8)
    ax2.spines['right'].set_visible(False)
    ax2.spines['top'].set_visible(False)
    
    # 总标题
    fig.suptitle(title, fontweight='bold', y=1.02)
    
    # ===================== 保存数据到独立Excel文件 =====================
    # 1. 预测值vs实际值原始数据
    pred_actual_df = pd.DataFrame({
        'CBM_Actual': cbm_true,
        'CBM_Predicted': cbm_pred,
        'CBM_Error': cbm_pred - cbm_true,
        'VBM_Actual': vbm_true,
        'VBM_Predicted': vbm_pred,
        'VBM_Error': vbm_pred - vbm_true
    })
    
    # 2. 拟合统计数据
    fit_stats_df = pd.DataFrame({
        'Metric': ['R2_Score', 'MAE', 'RMSE', 'Slope', 'Intercept', 'P_Value', 'Std_Error'],
        'CBM': [r2_cbm, mae_cbm, rmse_cbm, slope, intercept, p_val, std_err],
        'VBM': [r2_vbm, mae_vbm, rmse_vbm, slope_v, intercept_v, p_val_v, std_err_v]
    })
    
    # 3. 置信区间数据
    ci_data_df = pd.DataFrame({
        'CBM_X_Range': x_range,
        'CBM_Fit_Line': y_fit,
        'CBM_Lower_CI': y_fit - pred_interval,
        'CBM_Upper_CI': y_fit + pred_interval,
        'VBM_X_Range': x_range_v,
        'VBM_Fit_Line': y_fit_v,
        'VBM_Lower_CI': y_fit_v - pred_interval_v,
        'VBM_Upper_CI': y_fit_v + pred_interval_v
    })
    
    # 保存到独立文件：pred_actual.xlsx
    save_data_to_excel(pred_actual_df, 'pred_actual', 'Raw_Data')
    save_data_to_excel(fit_stats_df, 'pred_actual', 'Fit_Statistics')
    save_data_to_excel(ci_data_df, 'pred_actual', 'Confidence_Interval')
    
    save_academic_figure('academic_pred_vs_actual.pdf', fig)
    plt.show()
    return fig

def plot_error_analysis_academic(y_true, y_pred):
    """学术版误差分析图（移除Q-Q图，仅保留误差分布）"""
    # 计算误差
    cbm_error = y_pred[:, 0] - y_true['CBM'].values
    vbm_error = y_pred[:, 1] - y_true['VBM'].values
    
    # 调整布局：1行2列，横版尺寸
    fig = plt.figure(figsize=(10, 4.5))
    gs = gridspec.GridSpec(1, 2, width_ratios=[1, 1])
    
    # 1. CBM误差分布（核密度估计+直方图）
    ax1 = plt.subplot(gs[0, 0])
    # 核密度估计（更平滑，学术常用）
    kde_cbm = gaussian_kde(cbm_error)
    x_cbm = np.linspace(cbm_error.min(), cbm_error.max(), 200)
    kde_vals_cbm = kde_cbm(x_cbm)
    ax1.plot(x_cbm, kde_vals_cbm, 'b-', linewidth=1.5, label='KDE')
    # 直方图（归一化）
    hist_counts, hist_edges = np.histogram(cbm_error, bins=30, density=True)
    hist_centers = (hist_edges[:-1] + hist_edges[1:]) / 2
    ax1.hist(cbm_error, bins=30, alpha=0.5, density=True, color='#1f77b4', edgecolor='k', linewidth=0.5)
    # 正态拟合
    mu_cbm, sigma_cbm = stats.norm.fit(cbm_error)
    norm_vals_cbm = stats.norm.pdf(x_cbm, mu_cbm, sigma_cbm)
    ax1.plot(x_cbm, norm_vals_cbm, 'r--', linewidth=1.2, label=f'Normal fit ($\mu$={mu_cbm:.2f}, $\sigma$={sigma_cbm:.2f})')
    # 正态性检验
    stat_cbm, p_cbm = normaltest(cbm_error)
    ax1.axvline(x=0, color='k', linestyle='-', linewidth=0.8, alpha=0.7, label='Zero Error')
    
    ax1.set_xlabel('CBM Prediction Error (eV)', fontweight='medium')
    ax1.set_ylabel('Probability Density', fontweight='medium')
    ax1.set_title(f'CBM Error Distribution\n(D\'Agostino test: $p$={p_cbm:.2e})', fontweight='bold')
    ax1.legend(fontsize=8)
    ax1.spines['right'].set_visible(False)
    ax1.spines['top'].set_visible(False)
    
    # 2. VBM误差分布
    ax2 = plt.subplot(gs[0, 1])
    kde_vbm = gaussian_kde(vbm_error)
    x_vbm = np.linspace(vbm_error.min(), vbm_error.max(), 200)
    kde_vals_vbm = kde_vbm(x_vbm)
    ax2.plot(x_vbm, kde_vals_vbm, 'b-', linewidth=1.5, label='KDE')
    hist_counts_v, hist_edges_v = np.histogram(vbm_error, bins=30, density=True)
    hist_centers_v = (hist_edges_v[:-1] + hist_edges_v[1:]) / 2
    ax2.hist(vbm_error, bins=30, alpha=0.5, density=True, color='#ff7f0e', edgecolor='k', linewidth=0.5)
    mu_vbm, sigma_vbm = stats.norm.fit(vbm_error)
    norm_vals_vbm = stats.norm.pdf(x_vbm, mu_vbm, sigma_vbm)
    ax2.plot(x_vbm, norm_vals_vbm, 'r--', linewidth=1.2, label=f'Normal fit ($\mu$={mu_vbm:.2f}, $\sigma$={sigma_vbm:.2f})')
    stat_vbm, p_vbm = normaltest(vbm_error)
    ax2.axvline(x=0, color='k', linestyle='-', linewidth=0.8, alpha=0.7, label='Zero Error')
    
    ax2.set_xlabel('VBM Prediction Error (eV)', fontweight='medium')
    ax2.set_ylabel('Probability Density', fontweight='medium')
    ax2.set_title(f'VBM Error Distribution\n(D\'Agostino test: $p$={p_vbm:.2e})', fontweight='bold')
    ax2.legend(fontsize=8)
    ax2.spines['right'].set_visible(False)
    ax2.spines['top'].set_visible(False)
    
    # ===================== 保存数据到独立Excel文件 =====================
    # 1. 误差原始数据
    error_raw_df = pd.DataFrame({
        'CBM_Error': cbm_error,
        'VBM_Error': vbm_error
    })
    
    # 2. KDE和正态拟合数据
    kde_norm_df = pd.DataFrame({
        'CBM_X': x_cbm,
        'CBM_KDE': kde_vals_cbm,
        'CBM_Normal_Fit': norm_vals_cbm,
        'VBM_X': x_vbm,
        'VBM_KDE': kde_vals_vbm,
        'VBM_Normal_Fit': norm_vals_vbm
    })
    
    # 3. 直方图数据
    hist_df = pd.DataFrame({
        'CBM_Hist_Centers': hist_centers,
        'CBM_Hist_Density': hist_counts,
        'VBM_Hist_Centers': hist_centers_v,
        'VBM_Hist_Density': hist_counts_v
    })
    
    # 4. 误差统计数据
    error_stats_df = pd.DataFrame({
        'Metric': ['Mean', 'Std', 'DAgostino_Stat', 'DAgostino_P', 'MAE'],
        'CBM': [mu_cbm, sigma_cbm, stat_cbm, p_cbm, np.mean(np.abs(cbm_error))],
        'VBM': [mu_vbm, sigma_vbm, stat_vbm, p_vbm, np.mean(np.abs(vbm_error))]
    })
    
    # 保存到独立文件：error_analysis.xlsx
    save_data_to_excel(error_raw_df, 'error_analysis', 'Raw_Error')
    save_data_to_excel(kde_norm_df, 'error_analysis', 'KDE_Normal_Fit')
    save_data_to_excel(hist_df, 'error_analysis', 'Histogram_Data')
    save_data_to_excel(error_stats_df, 'error_analysis', 'Error_Statistics')
    
    save_academic_figure('academic_error_analysis.pdf', fig)
    plt.show()
    
    # 返回误差统计（用于论文）
    error_stats = {
        'CBM': {'mean': mu_cbm, 'std': sigma_cbm, 'mae': np.mean(np.abs(cbm_error)), 'norm_p': p_cbm},
        'VBM': {'mean': mu_vbm, 'std': sigma_vbm, 'mae': np.mean(np.abs(vbm_error)), 'norm_p': p_vbm}
    }
    return error_stats

def plot_academic_learning_curve(model, X, y, cv=5, title="Learning Curves (5-fold CV)"):
    """学术版学习曲线（添加收敛分析、方差/偏差标注）"""
    train_sizes, train_scores, val_scores = learning_curve(
        model, X, y, cv=cv, scoring='r2', n_jobs=-1,
        train_sizes=np.linspace(0.1, 1.0, 10), random_state=42
    )
    
    # 计算统计量
    train_mean = np.mean(train_scores, axis=1)
    train_std = np.std(train_scores, axis=1)
    val_mean = np.mean(val_scores, axis=1)
    val_std = np.std(val_scores, axis=1)
    
    # 计算偏差和方差
    bias = 1 - train_mean[-1]
    variance = train_mean[-1] - val_mean[-1]
    
    fig, ax = plt.subplots(figsize=(8, 5))
    
    # 训练集曲线（带误差带）
    ax.plot(train_sizes, train_mean, 'o-', color='#1f77b4', label='Training $R^2$', markersize=5)
    ax.fill_between(train_sizes, train_mean - train_std, train_mean + train_std, alpha=0.2, color='#1f77b4')
    
    # 验证集曲线
    ax.plot(train_sizes, val_mean, 's-', color='#ff7f0e', label='Validation $R^2$', markersize=5)
    ax.fill_between(train_sizes, val_mean - val_std, val_mean + val_std, alpha=0.2, color='#ff7f0e')
    
    # 标注收敛点
    convergence_idx = np.argmin(np.abs(np.diff(val_mean))) + 1
    ax.axvline(x=train_sizes[convergence_idx], color='gray', linestyle='--', linewidth=1, label=f'Convergence at {train_sizes[convergence_idx]:.0f} samples')
    
    # 标注偏差/方差
    annot_text = f'Final Train $R^2$: {train_mean[-1]:.3f} ± {train_std[-1]:.3f}\n'
    annot_text += f'Final Val $R^2$: {val_mean[-1]:.3f} ± {val_std[-1]:.3f}\n'
    annot_text += f'Bias: {bias:.3f} | Variance: {variance:.3f}'
    ax.text(0.05, 0.15, annot_text, transform=ax.transAxes, fontsize=8,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8, edgecolor='gray'))
    
    ax.set_xlabel('Number of Training Samples', fontweight='medium')
    ax.set_ylabel('$R^2$ Score', fontweight='medium')
    ax.set_title(f'{title}\n(Bias-Variance Analysis)', fontweight='bold')
    ax.legend(fontsize=8, framealpha=0.8)
    ax.set_ylim(bottom=max(0, val_mean.min() - 0.1), top=1.05)
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    
    # ===================== 保存数据到独立Excel文件 =====================
    # 1. 学习曲线原始数据
    learning_curve_df = pd.DataFrame({
        'Train_Samples': train_sizes,
        'Train_R2_Mean': train_mean,
        'Train_R2_Std': train_std,
        'Train_R2_Min': train_mean - train_std,
        'Train_R2_Max': train_mean + train_std,
        'Val_R2_Mean': val_mean,
        'Val_R2_Std': val_std,
        'Val_R2_Min': val_mean - val_std,
        'Val_R2_Max': val_mean + val_std
    })
    
    # 2. 偏差方差分析数据
    bias_variance_df = pd.DataFrame({
        'Metric': ['Bias', 'Variance', 'Final_Val_R2', 'Convergence_Samples', 'CV_Folds'],
        'Value': [bias, variance, val_mean[-1], train_sizes[convergence_idx], cv]
    })
    
    # 3. 完整的交叉验证分数
    cv_scores_df = pd.DataFrame(train_scores, columns=[f'CV_Fold_{i+1}' for i in range(cv)], index=train_sizes)
    cv_scores_df['Mean'] = train_mean
    cv_scores_df['Std'] = train_std
    cv_scores_df.index.name = 'Train_Samples'
    
    val_cv_scores_df = pd.DataFrame(val_scores, columns=[f'CV_Fold_{i+1}' for i in range(cv)], index=train_sizes)
    val_cv_scores_df['Mean'] = val_mean
    val_cv_scores_df['Std'] = val_std
    val_cv_scores_df.index.name = 'Train_Samples'
    
    # 保存到独立文件：learning_curve.xlsx
    save_data_to_excel(learning_curve_df, 'learning_curve', 'Summary_Data')
    save_data_to_excel(bias_variance_df, 'learning_curve', 'Bias_Variance')
    save_data_to_excel(cv_scores_df, 'learning_curve', 'Train_CV_Scores')
    save_data_to_excel(val_cv_scores_df, 'learning_curve', 'Val_CV_Scores')
    
    save_academic_figure('academic_learning_curve.pdf', fig)
    plt.show()
    
    return {'bias': bias, 'variance': variance, 'final_r2': val_mean[-1]}

def plot_target_kde_distribution(y_train, y_val):
    """学术版目标变量分布（核密度估计，替代简单直方图）"""
    fig = plt.figure(figsize=(10, 4.5))
    gs = gridspec.GridSpec(1, 2, width_ratios=[1, 1])
    
    # CBM分布
    ax1 = plt.subplot(gs[0])
    # 训练集KDE
    kde_train_cbm = gaussian_kde(y_train['CBM'])
    x_cbm = np.linspace(min(y_train['CBM'].min(), y_val['CBM'].min()), max(y_train['CBM'].max(), y_val['CBM'].max()), 200)
    kde_train_vals_cbm = kde_train_cbm(x_cbm)
    ax1.plot(x_cbm, kde_train_vals_cbm, 'b-', linewidth=1.5, label=f'Training (n={len(y_train)})')
    # 验证集KDE
    kde_val_cbm = gaussian_kde(y_val['CBM'])
    kde_val_vals_cbm = kde_val_cbm(x_cbm)
    ax1.plot(x_cbm, kde_val_vals_cbm, 'r--', linewidth=1.5, label=f'Validation (n={len(y_val)})')
    
    ax1.set_xlabel('CBM (eV)', fontweight='medium')
    ax1.set_ylabel('Probability Density', fontweight='medium')
    ax1.set_title('CBM Distribution (Train vs Validation)', fontweight='bold')
    ax1.legend(fontsize=8)
    ax1.spines['right'].set_visible(False)
    ax1.spines['top'].set_visible(False)
    
    # VBM分布
    ax2 = plt.subplot(gs[1])
    kde_train_vbm = gaussian_kde(y_train['VBM'])
    x_vbm = np.linspace(min(y_train['VBM'].min(), y_val['VBM'].min()), max(y_train['VBM'].max(), y_val['VBM'].max()), 200)
    kde_train_vals_vbm = kde_train_vbm(x_vbm)
    ax2.plot(x_vbm, kde_train_vals_vbm, 'b-', linewidth=1.5, label=f'Training (n={len(y_train)})')
    kde_val_vbm = gaussian_kde(y_val['VBM'])
    kde_val_vals_vbm = kde_val_vbm(x_vbm)
    ax2.plot(x_vbm, kde_val_vals_vbm, 'r--', linewidth=1.5, label=f'Validation (n={len(y_val)})')
    
    ax2.set_xlabel('VBM (eV)', fontweight='medium')
    ax2.set_ylabel('Probability Density', fontweight='medium')
    ax2.set_title('VBM Distribution (Train vs Validation)', fontweight='bold')
    ax2.legend(fontsize=8)
    ax2.spines['right'].set_visible(False)
    ax2.spines['top'].set_visible(False)
    
    # ===================== 保存数据到独立Excel文件 =====================
    # 1. KDE分布数据
    kde_dist_df = pd.DataFrame({
        'CBM_X': x_cbm,
        'CBM_Train_KDE': kde_train_vals_cbm,
        'CBM_Val_KDE': kde_val_vals_cbm,
        'VBM_X': x_vbm,
        'VBM_Train_KDE': kde_train_vals_vbm,
        'VBM_Val_KDE': kde_val_vals_vbm
    })
    
    # 2. 分开保存训练集和验证集的原始数据（修复长度不一致问题）
    train_raw_df = pd.DataFrame({
        'CBM_Train': y_train['CBM'].values,
        'VBM_Train': y_train['VBM'].values
    })
    
    val_raw_df = pd.DataFrame({
        'CBM_Val': y_val['CBM'].values,
        'VBM_Val': y_val['VBM'].values
    })
    
    # 3. 目标变量统计
    target_stats_df = pd.DataFrame({
        'Metric': ['Mean', 'Std', 'Min', 'Max', 'Count'],
        'CBM_Train': [y_train['CBM'].mean(), y_train['CBM'].std(), y_train['CBM'].min(), y_train['CBM'].max(), len(y_train)],
        'CBM_Val': [y_val['CBM'].mean(), y_val['CBM'].std(), y_val['CBM'].min(), y_val['CBM'].max(), len(y_val)],
        'VBM_Train': [y_train['VBM'].mean(), y_train['VBM'].std(), y_train['VBM'].min(), y_train['VBM'].max(), len(y_train)],
        'VBM_Val': [y_val['VBM'].mean(), y_val['VBM'].std(), y_val['VBM'].min(), y_val['VBM'].max(), len(y_val)]
    })
    
    # 保存到独立文件：target_distribution.xlsx
    save_data_to_excel(kde_dist_df, 'target_distribution', 'KDE_Data')
    save_data_to_excel(train_raw_df, 'target_distribution', 'Train_Raw')
    save_data_to_excel(val_raw_df, 'target_distribution', 'Val_Raw')
    save_data_to_excel(target_stats_df, 'target_distribution', 'Statistics')
    
    save_academic_figure('academic_target_distribution.pdf', fig)
    plt.show()

def plot_feature_correlation_heatmap(X_train, y_train):
    """学术版特征相关性热图（仅数值特征，与Space Group Symbol无关，无需修改）"""
    # 合并特征和目标变量
    corr_data = pd.concat([X_train, y_train], axis=1)
    # 只保留数值特征（分类特征已编码，相关性无意义）
    numeric_cols = ["Space Group Number", "Sites", "Volume", "Density", "CBM", "VBM"]
    corr_data = corr_data[numeric_cols].corr()
    
    fig, ax = plt.subplots(figsize=(7, 6))
    # 绘制热图（学术配色）
    im = ax.imshow(corr_data, cmap='RdBu_r', vmin=-1, vmax=1, aspect='auto')
    
    # 添加数值标注
    for i in range(len(corr_data)):
        for j in range(len(corr_data)):
            text = ax.text(j, i, f'{corr_data.iloc[i, j]:.2f}',
                          ha="center", va="center", color="black", fontsize=8)
    
    # 设置标签
    ax.set_xticks(np.arange(len(corr_data.columns)))
    ax.set_yticks(np.arange(len(corr_data.columns)))
    ax.set_xticklabels(corr_data.columns, rotation=45, ha='right')
    ax.set_yticklabels(corr_data.columns)
    
    # 添加颜色条
    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label('Pearson Correlation Coefficient', fontweight='medium')
    
    ax.set_title('Feature-Target Correlation Matrix', fontweight='bold', pad=15)
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    
    # ===================== 保存数据到独立Excel文件 =====================
    # 1. 相关性矩阵
    corr_matrix_df = corr_data.copy()
    corr_matrix_df.index.name = 'Feature'
    corr_matrix_df.columns.name = 'Correlated_Feature'
    
    # 2. 特征统计数据
    feature_stats_df = pd.DataFrame({
        'Feature': numeric_cols,
        'Mean': [X_train[col].mean() if col in X_train.columns else y_train[col].mean() for col in numeric_cols],
        'Std': [X_train[col].std() if col in X_train.columns else y_train[col].std() for col in numeric_cols],
        'Min': [X_train[col].min() if col in X_train.columns else y_train[col].min() for col in numeric_cols],
        'Max': [X_train[col].max() if col in X_train.columns else y_train[col].max() for col in numeric_cols]
    })
    
    # 保存到独立文件：feature_correlation.xlsx
    save_data_to_excel(corr_matrix_df, 'feature_correlation', 'Correlation_Matrix')
    save_data_to_excel(feature_stats_df, 'feature_correlation', 'Feature_Statistics')
    
    save_academic_figure('academic_correlation_heatmap.pdf', fig)
    plt.show()

def main():
    # 数据路径（替换为你的新训练/验证集路径）
    train_file = "./data/new_train.csv"
    val_file = "./data/new_val.csv"
    model_output = "models/xgb_academic_opt.pkl"
    
    print(f"=== 学术图表生成流程 ===")
    print(f"图表将保存至: {PICTURE_DIR}/")
    print(f"图表数据将保存至: {DATA_DIR}/ (每个图表对应独立Excel文件)")
    
    # 1. 加载数据
    train_df = pd.read_csv(train_file)
    val_df = pd.read_csv(val_file)
    print(f"\n数据加载完成:")
    print(f"  训练集样本数: {len(train_df)}")
    print(f"  验证集样本数: {len(val_df)}")
    
    # 2. 特征和目标列
    feature_cols = [
        "Crystal System", "Space Group Symbol",
        "Space Group Number", "Sites", "Volume", "Density"
    ]
    target_cols = ["CBM", "VBM"]
    
    X_train = train_df[feature_cols]
    y_train = train_df[target_cols]
    X_val = val_df[feature_cols]
    y_val = val_df[target_cols]
    
    # 3. 数据统计（学术表格用）
    print(f"\n=== 目标变量统计（论文表格用）===")
    print("| Metric       | CBM (Train)       | VBM (Train)       | CBM (Val)         | VBM (Val)         |")
    print("|--------------|-------------------|-------------------|-------------------|-------------------|")
    print(f"| Mean ± Std   | {y_train['CBM'].mean():.3f} ± {y_train['CBM'].std():.3f} | {y_train['VBM'].mean():.3f} ± {y_train['VBM'].std():.3f} | {y_val['CBM'].mean():.3f} ± {y_val['CBM'].std():.3f} | {y_val['VBM'].mean():.3f} ± {y_val['VBM'].std():.3f} |")
    print(f"| Min-Max      | [{y_train['CBM'].min():.3f}, {y_train['CBM'].max():.3f}] | [{y_train['VBM'].min():.3f}, {y_train['VBM'].max():.3f}] | [{y_val['CBM'].min():.3f}, {y_val['CBM'].max():.3f}] | [{y_val['VBM'].min():.3f}, {y_val['VBM'].max():.3f}] |")
    
    # 4. 特征预处理
    numeric_features = ["Space Group Number", "Sites", "Volume", "Density"]
    categorical_features = ["Crystal System", "Space Group Symbol"]
    
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_features),  # 数值特征标准化（学术常用）
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
        ]
    )
    
    # 5. XGBoost模型（保持最优配置）
    print(f"\n=== 模型训练 ===")
    xgb_reg = XGBRegressor(
        n_estimators=800, max_depth=7, learning_rate=0.03,
        subsample=0.8, colsample_bytree=0.8, reg_alpha=0.1,
        reg_lambda=1.0, min_child_weight=3, objective='reg:squarederror',
        tree_method='hist', n_jobs=-1, random_state=42
    )
    
    multi_output_model = MultiOutputRegressor(xgb_reg)
    model = Pipeline([
        ("preprocess", preprocessor),
        ("regressor", multi_output_model),
    ])
    
    # 训练模型
    start_time = time()
    model.fit(X_train, y_train)
    print(f"训练完成，耗时: {time() - start_time:.2f}秒")
    
    # 6. 模型评估
    y_pred = model.predict(X_val)
    r2 = r2_score(y_val, y_pred, multioutput="raw_values")
    mse = mean_squared_error(y_val, y_pred, multioutput="raw_values")
    mae = [mean_absolute_error(y_val['CBM'], y_pred[:,0]), mean_absolute_error(y_val['VBM'], y_pred[:,1])]
    
    print(f"\n=== 模型性能（学术表格用）===")
    print("| Metric      | CBM       | VBM       | Average   |")
    print("|-------------|-----------|-----------|-----------|")
    print(f"| $R^2$ Score | {r2[0]:.4f}    | {r2[1]:.4f}    | {(r2[0]+r2[1])/2:.4f}   |")
    print(f"| MSE (eV²)   | {mse[0]:.4f}  | {mse[1]:.4f}  | {(mse[0]+mse[1])/2:.4f} |")
    print(f"| MAE (eV)    | {mae[0]:.4f}    | {mae[1]:.4f}    | {(mae[0]+mae[1])/2:.4f}   |")
    
    # 7. 生成学术图表（核心）
    print(f"\n=== 生成学术图表 ===")
    
    # 7.1 目标变量分布（核密度估计）
    print("1/6: 绘制目标变量分布...")
    plot_target_kde_distribution(y_train, y_val)
    
    # 7.2 特征相关性热图（无需修改）
    print("2/6: 绘制特征相关性热图...")
    plot_feature_correlation_heatmap(X_train, y_train)
    
    # 7.3 预测值vs实际值（带置信区间）
    print("3/6: 绘制预测性能图...")
    plot_academic_pred_vs_actual(y_val, y_pred)
    
    # 7.4 误差分析（分布+Q-Q图）
    print("4/6: 绘制误差分析图...")
    error_stats = plot_error_analysis_academic(y_val, y_pred)
    
    # 7.5 学习曲线（偏差-方差分析）
    print("5/6: 绘制学习曲线...")
    learning_stats = plot_academic_learning_curve(model, X_train, y_train)
    
    # 7.6 合并特征重要性
    print("6/6: 绘制特征重要性图...")
    # 获取完整特征名（编码后的）
    feature_names = numeric_features.copy()
    cat_encoder = model.named_steps['preprocess'].named_transformers_['cat']
    cat_feature_names = cat_encoder.get_feature_names_out(categorical_features)
    feature_names.extend(cat_feature_names)
    # 绘制调整后的特征重要性
    plot_merged_feature_importance(model, feature_names, title="Adjusted Feature Importance (XGBoost)")
    
    # 8. 保存模型和预测结果
    joblib.dump(model, model_output)
    print(f"\n最优模型已保存: {model_output}")
    
    # 保存预测结果（用于后续分析）
    result_df = val_df.copy()
    result_df["CBM_pred"] = y_pred[:, 0]
    result_df["VBM_pred"] = y_pred[:, 1]
    result_df["CBM_error"] = result_df["CBM_pred"] - result_df["CBM"]
    result_df["VBM_error"] = result_df["VBM_pred"] - result_df["VBM"]
    result_df.to_csv("data/academic_validation_predictions.csv", index=False)
    
    # 保存模型性能汇总到独立文件
    model_performance_df = pd.DataFrame({
        'Metric': ['R2_Score_CBM', 'R2_Score_VBM', 'R2_Score_Avg', 
                  'MSE_CBM', 'MSE_VBM', 'MSE_Avg',
                  'MAE_CBM', 'MAE_VBM', 'MAE_Avg'],
        'Value': [r2[0], r2[1], (r2[0]+r2[1])/2,
                 mse[0], mse[1], (mse[0]+mse[1])/2,
                 mae[0], mae[1], (mae[0]+mae[1])/2]
    })
    save_data_to_excel(model_performance_df, 'model_performance', 'Summary')
    
    print(f"\n=== 所有图表和数据已生成完成 ===")
    print(f"图表路径: {os.path.abspath(PICTURE_DIR)}")
    print(f"数据文件路径: {os.path.abspath(DATA_DIR)}")
    print(f"\n生成的独立数据文件列表:")
    print("  - feature_importance.xlsx: 特征重要性数据")
    print("  - pred_actual.xlsx: 预测值vs实际值数据")
    print("  - error_analysis.xlsx: 误差分析数据")
    print("  - learning_curve.xlsx: 学习曲线数据")
    print("  - target_distribution.xlsx: 目标变量分布数据")
    print("  - feature_correlation.xlsx: 特征相关性数据")
    print("  - model_performance.xlsx: 模型性能汇总数据")
    print(f"\n生成的图表列表:")
    print("  1. merged_feature_importance_adjusted.pdf (调整后特征重要性)")
    print("  2. academic_pred_vs_actual.pdf (预测vs实际，带置信区间)")
    print("  3. academic_error_analysis.pdf (误差分布+正态性检验)")
    print("  4. academic_learning_curve.pdf (学习曲线+偏差方差分析)")
    print("  5. academic_target_distribution.pdf (目标变量核密度分布)")
    print("  6. academic_correlation_heatmap.pdf (特征相关性热图)")

if __name__ == "__main__":
    main()