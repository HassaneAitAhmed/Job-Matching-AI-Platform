#!/usr/bin/env python3
"""
Create placeholder images for README screenshots.
"""

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import numpy as np
    
    # Create time comparison chart
    fig, ax = plt.subplots(figsize=(12, 8))
    fig.patch.set_facecolor('white')
    
    algorithms = ['Greedy A*', 'CSP', 'A* with ML', 'Global Search', 'A* Assignment', 'Genetic Algorithm']
    times = [0.85, 1.20, 9.13, 22.10, 28.50, 45.30]
    colors = ['#2ecc71', '#3498db', '#9b59b6', '#e67e22', '#e74c3c', '#c0392b']
    
    bars = ax.barh(algorithms, times, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    
    # Add value labels
    for i, (bar, time) in enumerate(zip(bars, times)):
        width = bar.get_width()
        label_x = width + 1.5
        ax.text(label_x, bar.get_y() + bar.get_height()/2, 
                f'{time:.2f}s', 
                ha='left', va='center', fontsize=11, fontweight='bold')
    
    ax.set_xlabel('Execution Time (seconds)', fontsize=13, fontweight='bold')
    ax.set_ylabel('Algorithm', fontsize=13, fontweight='bold')
    ax.set_title('Algorithm Performance Comparison\nExecution Time for Job-Matching Tasks', 
                 fontsize=16, fontweight='bold', pad=20)
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    ax.set_xlim(0, max(times) * 1.15)
    
    # Add legend
    legend_labels = [
        '⚡ Very Fast (< 2s)',
        '🚀 Fast (2-10s)',
        '⏱️ Medium (10-30s)',
        '🐌 Slow (> 30s)'
    ]
    legend_colors = ['#2ecc71', '#9b59b6', '#e67e22', '#c0392b']
    legend_patches = [mpatches.Patch(color=color, label=label) 
                      for color, label in zip(legend_colors, legend_labels)]
    ax.legend(handles=legend_patches, loc='lower right', fontsize=10)
    
    plt.tight_layout()
    plt.savefig('screenshots/time_comparison.png', 
                dpi=150, bbox_inches='tight', facecolor='white')
    print("✓ Created: screenshots/time_comparison.png")
    plt.close()
    
    # Create search output example
    fig, ax = plt.subplots(figsize=(12, 10))
    fig.patch.set_facecolor('#f8f9fa')
    ax.axis('off')
    
    # Title
    title_text = "A* Heuristic Search with ML - Output Example"
    ax.text(0.5, 0.95, title_text, ha='center', va='top', 
            fontsize=18, fontweight='bold', transform=ax.transAxes)
    
    # Job Offer Section
    job_y = 0.88
    ax.text(0.05, job_y, "Job Offer Requirements:", ha='left', va='top',
            fontsize=14, fontweight='bold', transform=ax.transAxes,
            bbox=dict(boxstyle='round', facecolor='#3498db', alpha=0.3, pad=0.5))
    
    job_details = [
        "• Sector: Energy & Petroleum",
        "• Department: HSE (Health, Safety, Environment)",
        "• Location: Algiers",
        "• Required Skills: Risk Assessment, Reporting, Team Leadership",
        "• Min Experience: 3 years",
        "• Education Level: Licence",
        "• Salary Range: $40,000 - $60,000"
    ]
    
    y_offset = job_y - 0.03
    for detail in job_details:
        ax.text(0.08, y_offset, detail, ha='left', va='top',
                fontsize=11, transform=ax.transAxes, family='monospace')
        y_offset -= 0.03
    
    # Top Matches Section
    matches_y = y_offset - 0.05
    ax.text(0.05, matches_y, "Top 5 Matching Candidates:", ha='left', va='top',
            fontsize=14, fontweight='bold', transform=ax.transAxes,
            bbox=dict(boxstyle='round', facecolor='#2ecc71', alpha=0.3, pad=0.5))
    
    # Match 1
    y_pos = matches_y - 0.05
    match_colors = ['#27ae60', '#2ecc71', '#52be80', '#7dcea0', '#a9dfbf']
    match_scores = ['94.5%', '91.2%', '88.7%', '86.3%', '84.1%']
    
    for i, (color, score) in enumerate(zip(match_colors, match_scores), 1):
        # Candidate header
        ax.text(0.08, y_pos, f"#{i} Employee ID: {523 * i}", ha='left', va='top',
                fontsize=12, fontweight='bold', transform=ax.transAxes,
                bbox=dict(boxstyle='round', facecolor=color, alpha=0.4, pad=0.3))
        
        # Compatibility score
        ax.text(0.70, y_pos, f"Compatibility: {score}", ha='left', va='top',
                fontsize=12, fontweight='bold', transform=ax.transAxes,
                color='#27ae60')
        
        y_pos -= 0.03
        
        # Details
        details = [
            f"   Skills Match: {100 if i <= 3 else 67}% | Experience: {9-i} years | Education: {'Master' if i % 2 else 'Doctorate'}",
            f"   Sector: Energy & Petroleum | Location: Algiers",
        ]
        
        for detail in details:
            ax.text(0.08, y_pos, detail, ha='left', va='top',
                    fontsize=10, transform=ax.transAxes, family='monospace')
            y_pos -= 0.025
        
        y_pos -= 0.02
    
    # Footer
    footer_y = 0.05
    ax.text(0.5, footer_y, 
            "Algorithm: A* Heuristic Search | Execution Time: 9.13 seconds | Candidates Evaluated: 10,000",
            ha='center', va='bottom', fontsize=10, style='italic',
            transform=ax.transAxes, color='#7f8c8d')
    
    plt.tight_layout()
    plt.savefig('screenshots/search_output.png',
                dpi=150, bbox_inches='tight', facecolor='#f8f9fa')
    print("✓ Created: screenshots/search_output.png")
    plt.close()
    
    print("\n✅ Screenshot placeholders created successfully!")
    print("\nNote: These are example screenshots. To get real screenshots:")
    print("1. Run the actual algorithms")
    print("2. Capture the terminal output or visualizations")
    print("3. Replace these placeholder images with actual screenshots")
    
except ImportError:
    print("matplotlib is required to create screenshots")
    print("Run: pip install matplotlib")
except Exception as e:
    print(f"Error creating screenshots: {e}")
