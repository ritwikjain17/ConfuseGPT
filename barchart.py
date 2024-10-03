import matplotlib.pyplot as plt
import numpy as np

augmentations = ("Original", "Unit Perturbation")
accuracies = {
    "GPT3.5-Turbo": (80.89, 23.24),
    "Haiku": (73.44, 15.93),
}

x = np.arange(len(augmentations))  # the label locations
width = 0.25  # the width of the bars
multiplier = 0

fig, ax = plt.subplots(layout='constrained')

for attribute, measurement in accuracies.items():
    offset = width * multiplier
    rects = ax.bar(x + offset, measurement, width, label=attribute)
    ax.bar_label(rects, padding=3)
    multiplier += 1

# Add some text for labels, title and custom x-axis tick labels, etc.
ax.set_ylabel('Accuracy (%)')
ax.set_title('Effect on accuracy of unit augmentations')
ax.set_xticks(x + width / 2, augmentations)
ax.legend(loc='upper left', ncols=3)
ax.set_ylim(0, 115)

plt.show()
