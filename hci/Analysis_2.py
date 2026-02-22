import pandas as pd
import numpy as np
from scipy import stats
import sys


def analyze_trust_study(main_data_file, survey_data_file):
    """
    Analyzes trust study data from CSV files

    Args:
        main_data_file: Path to main study data CSV (from Google Sheets)
        survey_data_file: Path to exit survey data CSV (from Google Forms)
    """

    # Load the data
    print("Loading data files...")
    main_df = pd.read_csv(main_data_file)
    survey_df = pd.read_csv(survey_data_file)

    # Clean column names (remove spaces)
    main_df.columns = main_df.columns.str.strip()
    survey_df.columns = survey_df.columns.str.strip()

    print(f"Loaded {len(main_df)} participants from main data")
    print(f"Loaded {len(survey_df)} survey responses\n")

    print("=" * 60)
    print("TRUST CALIBRATION STUDY - ANALYSIS RESULTS")
    print("=" * 60)
    print(f"Total Participants: {len(main_df)}\n")

    # Calculate mean trust scores for each participant
    trust_a_cols = ['trustA_q1', 'trustA_q2', 'trustA_q3', 'trustA_q4', 'trustA_q5']
    trust_b_cols = ['trustB_q1', 'trustB_q2', 'trustB_q3', 'trustB_q4', 'trustB_q5']

    main_df['trust_A_mean'] = main_df[trust_a_cols].mean(axis=1)
    main_df['trust_B_mean'] = main_df[trust_b_cols].mean(axis=1)

    # Map to display types
    main_df['trust_static'] = main_df.apply(
        lambda row: row['trust_A_mean'] if row['systemA_display'] == 'static' else row['trust_B_mean'],
        axis=1
    )
    main_df['trust_adaptive'] = main_df.apply(
        lambda row: row['trust_A_mean'] if row['systemA_display'] == 'adaptive' else row['trust_B_mean'],
        axis=1
    )

    # 1. DESCRIPTIVE STATISTICS
    print("1. DESCRIPTIVE STATISTICS")
    print("-" * 40)
    print(
        f"Trust in Static Display:    M = {main_df['trust_static'].mean():.2f} (SD = {main_df['trust_static'].std():.2f})")
    print(
        f"Trust in Adaptive Display:  M = {main_df['trust_adaptive'].mean():.2f} (SD = {main_df['trust_adaptive'].std():.2f})")
    print()

    # 2. PREFERENCE ANALYSIS
    print("2. PREFERENCE ANALYSIS")
    print("-" * 40)

    # Map preferences to display types
    adaptive_pref = 0
    static_pref = 0
    none_pref = 0

    for _, row in main_df.iterrows():
        if pd.isna(row['preference']) or row['preference'] == 'none':
            none_pref += 1
        elif row['preference'] == 'A' and row['systemA_display'] == 'adaptive':
            adaptive_pref += 1
        elif row['preference'] == 'A' and row['systemA_display'] == 'static':
            static_pref += 1
        elif row['preference'] == 'B' and row['systemB_display'] == 'adaptive':
            adaptive_pref += 1
        elif row['preference'] == 'B' and row['systemB_display'] == 'static':
            static_pref += 1

    total_with_pref = adaptive_pref + static_pref
    if total_with_pref > 0:
        print(
            f"Preferred Adaptive Display: {adaptive_pref}/{total_with_pref} ({adaptive_pref / total_with_pref * 100:.1f}%)")
        print(
            f"Preferred Static Display:   {static_pref}/{total_with_pref} ({static_pref / total_with_pref * 100:.1f}%)")
        if none_pref > 0:
            print(f"No Preference:              {none_pref}")
    print()

    # 3. STATISTICAL TEST
    print("3. STATISTICAL TEST (Paired t-test)")
    print("-" * 40)

    # Remove any NaN values for t-test
    valid_trust = main_df[['trust_static', 'trust_adaptive']].dropna()

    if len(valid_trust) > 0:
        t_stat, p_value = stats.ttest_rel(valid_trust['trust_static'], valid_trust['trust_adaptive'])

        # Cohen's d
        diff = valid_trust['trust_static'] - valid_trust['trust_adaptive']
        cohen_d = diff.mean() / diff.std() if diff.std() > 0 else 0

        print(f"t({len(valid_trust) - 1}) = {t_stat:.3f}, p = {p_value:.3f}")
        print(f"Cohen's d = {cohen_d:.3f}")

        if p_value < 0.05:
            print("Result: SIGNIFICANT difference between displays")
        else:
            print("Result: NO significant difference between displays")
    print()

    # 4. MANIPULATION CHECK (from survey data)
    print("4. MANIPULATION CHECK")
    print("-" * 40)

    # Check if the manipulation check column exists
    manip_columns = ['What was the main difference between System A and System B?',
                     'Main difference between systems',
                     'Manipulation Check']

    manip_col = None
    for col in manip_columns:
        if col in survey_df.columns:
            manip_col = col
            break

    if manip_col:
        correct_answer = 'How they displayed confidence information'
        correct = (survey_df[manip_col] == correct_answer).sum()
        total_survey = len(survey_df)

        print(
            f"Correctly identified display as main difference: {correct}/{total_survey} ({correct / total_survey * 100:.1f}%)")

        # Show what people thought
        print("\nResponses:")
        for response in survey_df[manip_col].value_counts().items():
            print(f"  - {response[0]}: {response[1]}")
    else:
        print("Manipulation check column not found in survey data")
    print()

    # 5. ORDER EFFECTS
    print("5. ORDER EFFECTS ANALYSIS")
    print("-" * 40)

    # Check if seeing static first affects preference
    static_first = main_df[main_df['systemA_display'] == 'static']
    adaptive_first = main_df[main_df['systemA_display'] == 'adaptive']

    if len(static_first) > 0:
        print(f"When Static shown first (n={len(static_first)}):")
        print(f"  - Trust in Static: M={static_first['trust_static'].mean():.2f}")
        print(f"  - Trust in Adaptive: M={static_first['trust_adaptive'].mean():.2f}")
        print(f"  - Preferred Adaptive: {(static_first['preference'] == 'B').sum()}/{len(static_first)}")

    if len(adaptive_first) > 0:
        print(f"\nWhen Adaptive shown first (n={len(adaptive_first)}):")
        print(f"  - Trust in Static: M={adaptive_first['trust_static'].mean():.2f}")
        print(f"  - Trust in Adaptive: M={adaptive_first['trust_adaptive'].mean():.2f}")
        print(f"  - Preferred Static: {(adaptive_first['preference'] == 'B').sum()}/{len(adaptive_first)}")
    print()

    # 6. DEMOGRAPHICS (from survey)
    if 'Age' in survey_df.columns:
        print("6. DEMOGRAPHICS")
        print("-" * 40)
        print("Age distribution:")
        print(survey_df['Age'].value_counts())
        print()

    if 'How tech-savvy do you consider yourself?' in survey_df.columns:
        tech_col = 'How tech-savvy do you consider yourself?'
        print(f"Tech-savviness: M={survey_df[tech_col].mean():.2f}, SD={survey_df[tech_col].std():.2f}")
        print()

    # 7. KEY FINDINGS SUMMARY
    print("=" * 60)
    print("KEY FINDINGS SUMMARY")
    print("=" * 60)

    if total_with_pref > 0:
        print(f"✓ {adaptive_pref / total_with_pref * 100:.0f}% of participants preferred adaptive display")
    print(
        f"✓ Trust scores: Static={main_df['trust_static'].mean():.2f}, Adaptive={main_df['trust_adaptive'].mean():.2f}")

    if manip_col and total_survey > 0:
        print(f"✓ {correct / total_survey * 100:.0f}% passed manipulation check")

    if len(valid_trust) > 0:
        if p_value < 0.05:
            print(f"✓ Significant difference in trust (p={p_value:.3f})")
        else:
            print(f"✓ No significant difference in trust (p={p_value:.3f})")

    print("\n" + "=" * 60)
    print("RESULTS FOR PAPER")
    print("=" * 60)

    # Generate text for results section
    print("\nCopy this for your Results section:\n")
    print(f"A total of N={len(main_df)} participants completed the study. ", end="")

    if manip_col and total_survey > 0:
        print(f"The manipulation check revealed that {correct}/{total_survey} ({correct / total_survey * 100:.0f}%) "
              f"correctly identified that the systems differed in confidence display format. ", end="")

    print(f"\n\nTrust scores were similar between display types. Participants rated static displays "
          f"(M={main_df['trust_static'].mean():.2f}, SD={main_df['trust_static'].std():.2f}) and adaptive displays "
          f"(M={main_df['trust_adaptive'].mean():.2f}, SD={main_df['trust_adaptive'].std():.2f}) nearly identically. ",
          end="")

    if len(valid_trust) > 0:
        print(f"A paired-samples t-test revealed {'a significant' if p_value < 0.05 else 'no significant'} difference, "
              f"t({len(valid_trust) - 1})={t_stat:.2f}, p={p_value:.3f}, d={cohen_d:.3f}. ", end="")

    if total_with_pref > 0:
        print(f"\n\nDespite similar trust scores, {adaptive_pref / total_with_pref * 100:.0f}% of participants "
              f"preferred the adaptive display when forced to choose.")

    print("\n" + "=" * 60)

    # Save processed data
    output_df = main_df[['participantId', 'systemA_display', 'systemB_display',
                         'preference', 'trust_static', 'trust_adaptive',
                         'trust_A_mean', 'trust_B_mean']]
    output_df.to_csv('processed_results.csv', index=False)
    print("\n✓ Processed data saved to 'processed_results.csv'")

    # Create visualizations
    create_visualizations(main_df, survey_df)

    return main_df


def create_visualizations(main_df, survey_df):
    """
    Creates publication-quality visualizations for the paper and presentation
    """
    import matplotlib.pyplot as plt
    import seaborn as sns

    # Set style for better-looking plots
    plt.style.use('default')
    sns.set_palette("Set2")

    # Create figure with subplots
    fig = plt.figure(figsize=(15, 10))

    # 1. Trust Score Comparison (Box plot + points)
    ax1 = plt.subplot(2, 3, 1)
    trust_data = pd.DataFrame({
        'Static': main_df['trust_static'],
        'Adaptive': main_df['trust_adaptive']
    })

    # Create box plot
    bp = ax1.boxplot([trust_data['Static'].dropna(), trust_data['Adaptive'].dropna()],
                     labels=['Static', 'Adaptive'],
                     patch_artist=True,
                     notch=True,
                     showmeans=True)

    # Color the boxes
    colors = ['#8dd3c7', '#bebada']
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    # Add individual points
    for i, (col, data) in enumerate(trust_data.items(), 1):
        y = data.dropna()
        x = np.random.normal(i, 0.04, size=len(y))
        ax1.scatter(x, y, alpha=0.4, s=30)

    ax1.set_ylabel('Trust Score (1-7)', fontsize=12)
    ax1.set_title('Trust Scores by Display Type', fontsize=14, fontweight='bold')
    ax1.set_ylim(0.5, 7.5)
    ax1.grid(axis='y', alpha=0.3)

    # Add mean values as text
    ax1.text(1, 7.2, f"M={main_df['trust_static'].mean():.2f}", ha='center', fontsize=10)
    ax1.text(2, 7.2, f"M={main_df['trust_adaptive'].mean():.2f}", ha='center', fontsize=10)

    # 2. Preference Distribution (Bar chart)
    ax2 = plt.subplot(2, 3, 2)

    # Calculate preferences
    adaptive_pref = 0
    static_pref = 0
    for _, row in main_df.iterrows():
        if pd.notna(row['preference']):
            if row['preference'] == 'A' and row['systemA_display'] == 'adaptive':
                adaptive_pref += 1
            elif row['preference'] == 'A' and row['systemA_display'] == 'static':
                static_pref += 1
            elif row['preference'] == 'B' and row['systemB_display'] == 'adaptive':
                adaptive_pref += 1
            elif row['preference'] == 'B' and row['systemB_display'] == 'static':
                static_pref += 1

    pref_data = pd.DataFrame({
        'Display Type': ['Adaptive', 'Static'],
        'Count': [adaptive_pref, static_pref]
    })

    bars = ax2.bar(pref_data['Display Type'], pref_data['Count'],
                   color=['#bebada', '#8dd3c7'], edgecolor='black', linewidth=1.5)

    # Add percentage labels on bars
    total = adaptive_pref + static_pref
    if total > 0:
        for bar, count in zip(bars, pref_data['Count']):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width() / 2., height,
                     f'{count}\n({count / total * 100:.0f}%)',
                     ha='center', va='bottom', fontsize=11, fontweight='bold')

    ax2.set_ylabel('Number of Participants', fontsize=12)
    ax2.set_title('Display Preference', fontsize=14, fontweight='bold')
    ax2.set_ylim(0, max(adaptive_pref, static_pref) * 1.3)
    ax2.grid(axis='y', alpha=0.3)

    # 3. Individual Differences (Paired plot)
    ax3 = plt.subplot(2, 3, 3)

    # Plot lines connecting each participant's scores
    for idx, row in main_df.iterrows():
        ax3.plot([1, 2], [row['trust_static'], row['trust_adaptive']],
                 'o-', alpha=0.5, markersize=6)

    ax3.set_xticks([1, 2])
    ax3.set_xticklabels(['Static', 'Adaptive'])
    ax3.set_ylabel('Trust Score', fontsize=12)
    ax3.set_title('Individual Trust Changes', fontsize=14, fontweight='bold')
    ax3.set_ylim(0.5, 7.5)
    ax3.grid(axis='y', alpha=0.3)

    # 4. Manipulation Check (Pie chart)
    ax4 = plt.subplot(2, 3, 4)

    # Get manipulation check data
    manip_columns = ['What was the main difference between System A and System B?',
                     'Main difference between systems',
                     'Manipulation Check']

    manip_col = None
    for col in manip_columns:
        if col in survey_df.columns:
            manip_col = col
            break

    if manip_col:
        correct_answer = 'How they displayed confidence information'
        correct = (survey_df[manip_col] == correct_answer).sum()
        incorrect = len(survey_df) - correct

        wedges, texts, autotexts = ax4.pie([correct, incorrect],
                                           labels=['Correct', 'Incorrect'],
                                           colors=['#90EE90', '#FFB6C1'],
                                           autopct='%1.0f%%',
                                           startangle=90)

        # Make percentage text bold
        for autotext in autotexts:
            autotext.set_fontweight('bold')
            autotext.set_fontsize(12)

    ax4.set_title('Manipulation Check Results', fontsize=14, fontweight='bold')

    # 5. Trust by Order (Grouped bar chart)
    ax5 = plt.subplot(2, 3, 5)

    static_first = main_df[main_df['systemA_display'] == 'static']
    adaptive_first = main_df[main_df['systemA_display'] == 'adaptive']

    order_data = {
        'Static First': [static_first['trust_static'].mean(),
                         static_first['trust_adaptive'].mean()],
        'Adaptive First': [adaptive_first['trust_static'].mean(),
                           adaptive_first['trust_adaptive'].mean()]
    }

    x = np.arange(2)
    width = 0.35

    bars1 = ax5.bar(x - width / 2, order_data['Static First'], width,
                    label='Static First', color='#8dd3c7')
    bars2 = ax5.bar(x + width / 2, order_data['Adaptive First'], width,
                    label='Adaptive First', color='#bebada')

    ax5.set_xlabel('Display Type', fontsize=12)
    ax5.set_ylabel('Trust Score', fontsize=12)
    ax5.set_title('Order Effects', fontsize=14, fontweight='bold')
    ax5.set_xticks(x)
    ax5.set_xticklabels(['Static', 'Adaptive'])
    ax5.legend()
    ax5.set_ylim(0, 7)
    ax5.grid(axis='y', alpha=0.3)

    # 6. Demographics - Tech Savviness
    ax6 = plt.subplot(2, 3, 6)

    if 'How tech-savvy do you consider yourself?' in survey_df.columns:
        tech_col = 'How tech-savvy do you consider yourself?'
        tech_scores = survey_df[tech_col].dropna()

        ax6.hist(tech_scores, bins=np.arange(0.5, 8.5, 1),
                 color='#fbb4ae', edgecolor='black', linewidth=1.2)
        ax6.axvline(tech_scores.mean(), color='red', linestyle='--',
                    linewidth=2, label=f'Mean: {tech_scores.mean():.1f}')

        ax6.set_xlabel('Tech Savviness (1-7)', fontsize=12)
        ax6.set_ylabel('Frequency', fontsize=12)
        ax6.set_title('Participant Tech Savviness', fontsize=14, fontweight='bold')
        ax6.legend()
        ax6.grid(axis='y', alpha=0.3)

    plt.suptitle('Trust Calibration Study Results', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()

    # Save figure
    plt.savefig('trust_study_visualizations.png', dpi=300, bbox_inches='tight')
    plt.savefig('trust_study_visualizations.pdf', dpi=300, bbox_inches='tight')  # PDF for paper
    print("\n✓ Visualizations saved as 'trust_study_visualizations.png' and '.pdf'")

    # Create separate presentation slides
    create_presentation_figures(main_df, survey_df)

    plt.show()


def create_presentation_figures(main_df, survey_df):
    """
    Creates individual figures optimized for presentation slides
    """
    import matplotlib.pyplot as plt
    import seaborn as sns

    # Set style for presentations
    plt.style.use('default')
    sns.set_context("talk")  # Larger text for presentations

    # Figure 1: Main Result - Trust Comparison
    fig1, ax1 = plt.subplots(figsize=(10, 7))

    # Calculate means
    static_mean = main_df['trust_static'].mean()
    adaptive_mean = main_df['trust_adaptive'].mean()
    static_std = main_df['trust_static'].std()
    adaptive_std = main_df['trust_adaptive'].std()

    # Create bar plot with error bars
    bars = ax1.bar(['Static Display', 'Adaptive Display'],
                   [static_mean, adaptive_mean],
                   yerr=[static_std, adaptive_std],
                   capsize=10,
                   color=['#8dd3c7', '#bebada'],
                   edgecolor='black',
                   linewidth=2)

    # FIXED: Add value labels with proper padding
    for bar, mean, std in zip(bars, [static_mean, adaptive_mean], [static_std, adaptive_std]):
        height = bar.get_height()
        # Increased padding from 0.1 to 0.3 for better spacing
        ax1.text(bar.get_x() + bar.get_width() / 2., height + std + 0.3,
                 f'M = {mean:.2f}',
                 ha='center', va='bottom', fontsize=18, fontweight='bold')

    ax1.set_ylabel('Trust Score (1-7)', fontsize=16, fontweight='bold')
    # FIXED: Increased ylim from 7 to 7.5 to give more room at the top
    ax1.set_ylim(0, 7.5)
    ax1.set_title('Trust Scores: No Significant Difference', fontsize=20, fontweight='bold', pad=20)
    ax1.grid(axis='y', alpha=0.3)

    # FIXED: Moved statistical result text lower to avoid overlap
    ax1.text(0.5, 0.9, 'p = .989 (n.s.)',
             transform=ax1.transAxes, fontsize=16,
             ha='center', style='italic')

    plt.tight_layout()
    plt.savefig('slide_trust_comparison.png', dpi=150, bbox_inches='tight')

    # Figure 2: User Preference
    fig2, ax2 = plt.subplots(figsize=(10, 7))

    # Calculate preferences
    adaptive_pref = 0
    static_pref = 0
    for _, row in main_df.iterrows():
        if pd.notna(row['preference']):
            if row['preference'] == 'A' and row['systemA_display'] == 'adaptive':
                adaptive_pref += 1
            elif row['preference'] == 'A' and row['systemA_display'] == 'static':
                static_pref += 1
            elif row['preference'] == 'B' and row['systemB_display'] == 'adaptive':
                adaptive_pref += 1
            elif row['preference'] == 'B' and row['systemB_display'] == 'static':
                static_pref += 1

    total = adaptive_pref + static_pref
    if total > 0:
        sizes = [adaptive_pref / total * 100, static_pref / total * 100]
        labels = [f'Adaptive\n({adaptive_pref / total * 100:.0f}%)',
                  f'Static\n({static_pref / total * 100:.0f}%)']
        colors = ['#bebada', '#8dd3c7']

        wedges, texts, autotexts = ax2.pie(sizes, labels=labels, colors=colors,
                                           autopct='%1.0f%%', startangle=90,
                                           textprops={'fontsize': 18, 'fontweight': 'bold'})

        # Hide percentage (already in labels)
        for autotext in autotexts:
            autotext.set_text('')

        ax2.set_title('User Preference: Adaptive Wins', fontsize=20, fontweight='bold', pad=20)

    plt.tight_layout()
    plt.savefig('slide_preference.png', dpi=150, bbox_inches='tight')

    # ADDITIONAL: Create a cleaner version for the paper figure
    fig3, ax3 = plt.subplots(figsize=(8, 6))

    # Bar plot for paper
    bars = ax3.bar(['Static Display', 'Adaptive Display'],
                   [static_mean, adaptive_mean],
                   yerr=[static_std, adaptive_std],
                   capsize=8,
                   color=['#8dd3c7', '#bebada'],
                   edgecolor='black',
                   linewidth=1.5,
                   error_kw={'linewidth': 1.5})

    # Add value labels with proper spacing for paper
    for bar, mean in zip(bars, [static_mean, adaptive_mean]):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width() / 2., 6.8,
                 f'M = {mean:.2f}',
                 ha='center', va='bottom', fontsize=12, fontweight='bold')

    ax3.set_ylabel('Trust Score', fontsize=12)
    ax3.set_ylim(0, 7.5)
    ax3.set_title('Trust Scores by Display Type', fontsize=14, fontweight='bold')
    ax3.grid(axis='y', alpha=0.3, linestyle='--')

    # Add error bar labels
    ax3.text(0.5, -0.5, f'Error bars represent ±1 SD',
             transform=ax3.transData, fontsize=9,
             ha='center', style='italic', color='gray')

    # Add sample size
    ax3.text(0.98, 0.02, f'N = {len(main_df)}',
             transform=ax3.transAxes, fontsize=10,
             ha='right', va='bottom')

    plt.tight_layout()
    plt.savefig('trust_comparison.png', dpi=300, bbox_inches='tight')
    plt.savefig('trust_comparison.pdf', dpi=300, bbox_inches='tight')

    print("✓ Presentation slides saved as 'slide_trust_comparison.png' and 'slide_preference.png'")
    print("✓ Paper figure saved as 'trust_comparison.png' and 'trust_comparison.pdf'")

    plt.show()


# Main execution
if __name__ == "__main__":
    import sys
    import os

    # Default file names
    main_file = "study_data.csv"
    survey_file = "exit_survey.csv"

    # Check if files were provided as arguments
    if len(sys.argv) > 2:
        main_file = sys.argv[1]
        survey_file = sys.argv[2]

    # Check if files exist
    if not os.path.exists(main_file):
        print(f"ERROR: Could not find '{main_file}'")
        print("\nUsage: python analyze_trust.py [main_data.csv] [survey_data.csv]")
        print("\nOr ensure you have:")
        print("  - study_data.csv (from Google Sheets)")
        print("  - exit_survey.csv (from Google Forms)")
        sys.exit(1)

    if not os.path.exists(survey_file):
        print(f"ERROR: Could not find '{survey_file}'")
        print("\nUsage: python analyze_trust.py [main_data.csv] [survey_data.csv]")
        sys.exit(1)

    # Run analysis
    print(f"Analyzing files: {main_file} and {survey_file}\n")
    df = analyze_trust_study(main_file, survey_file)