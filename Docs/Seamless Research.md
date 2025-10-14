Below is a robust approach for improving the seam‑checking logic in your KS Seamless app.  Since your current algorithm sometimes misses seams, the goal is to detect when an image is truly tileable along the x‑axis, y‑axis or both.  Recent academic work highlights what properties a “tileability” metric must have, and those insights can guide our design.

---

## Key Insights from Research

* A model for measuring tileability must detect **local discontinuities** at image borders, handle images of **any dimension**, and capture **global patterns** (to spot repeating artifacts).  In the 2024 TexTile paper, the authors achieve this by tiling the input texture once in each dimension (creating a 2×2 grid) and then inspecting the concatenated image.  Their model uses a convolutional + self‑attention network to spot discontinuities and global patterns.  We don’t need deep learning for a simple checker, but the strategy of **duplicating the image and analysing the internal seams** is still highly relevant.

* The same paper notes that one must detect seams at multiple scales; local pixel differences alone may not reveal subtle discontinuities.  Multi‑scale analysis helps because seams sometimes become visible only at reduced resolution (blurring highlights overall tonal mismatch).

---

## Practical Algorithm for Seam Checking

1. **Pre‑processing**

   * Convert the image to a perceptually uniform colour space such as Lab; this reduces sensitivity to lighting differences and makes error measures more meaningful.
   * Optionally downsample the image into a pyramid (e.g. original, ½, and ¼ resolution) to perform multi‑scale checks.

2. **Build a 2×2 tiled composite**

   * Following the TexTile insight, create a new canvas that repeats the original image twice in both x and y directions.  The composite will look like:

     ```
     A B
     C D
     ```

     where each block is the same image.  The internal seams in this 2×2 grid are where discontinuities will appear if the texture is not tileable.

3. **Compute seam error along boundaries**

   * **Horizontal check:** compare the top row of pixels of the original image with the bottom row.  Compute a difference metric such as **mean absolute difference (MAD)** or **root mean squared error (RMSE)**.  You can extend this to compare the top k rows and bottom k rows (e.g. 5–10 pixels) and average the error along the entire width.
   * **Vertical check:** similarly compare the first column(s) and last column(s).
   * **2×2 composite check:** compute the difference along the interior seams of the tiled composite (middle horizontal and vertical seams).  This exposes mismatches that may not be obvious at the outer edges if the image has strong gradients.
   * **Cross‑correlation**: in addition to pixel‑wise differences, compute the **normalized cross‑correlation** between the opposing edges.  A correlation close to 1 indicates similar patterns and colours.

4. **Edge/gradient analysis (optional)**

   * Perform **Canny edge detection** on the image and on the 2×2 composite.  If the image is tileable, the edge map should be continuous across the seams.  Count the number of edge pixels that end at the seam and divide by the seam length; a higher count implies a visible seam.  Combine this with color difference measures for robustness.

5. **Thresholding & scoring**

   * Normalize error values by the dynamic range of the Lab channels.  Define thresholds empirically: for example, if the normalized MAD is below 0.02 and cross‑correlation above 0.95 at all scales, treat the axis as seamless.  If horizontal and vertical tests both pass, mark the image as seamless in both directions; if only one axis passes, mark accordingly.

6. **Visual feedback**

   * To replicate the helpful visual overlay seen on pycheung.com, generate a preview that shows the 2×2 tiled composite and highlights seams in red where the error exceeds the threshold.  Users can then see exactly where seams occur.

7. **Advanced option (data‑driven metric)**

   * If you need a more objective, generalizable measure, consider adopting the **TexTile metric**.  Their method tilts the image once across both dimensions and feeds the result to a neural classifier that outputs a tileability score.  The source code and pretrained model are open‑source.  Implementing this would give you a single scalar (0–1) representing tileability; values near 1 indicate seamless textures, while values near 0 flag non‑tileable images.  This is heavy for a simple desktop app but could be offered as an optional “AI‑assisted” check.

---

## Summary of Recommended Steps

| Step                                                         | Purpose                                                                                                      |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------ |
| Convert image to Lab and downsample to multiple scales       | Ensure that color differences reflect perceived differences; capture seams visible at different resolutions. |
| Create a 2×2 tiled composite (as TexTile does)               | Exposes seams across both axes and helps detect repeating patterns.                                          |
| Measure MAD/RMSE between opposite edges at each scale        | Quantifies color/tonal mismatches along the edges.                                                           |
| Compute cross‑correlation and optional edge map comparison   | Detects structural alignment and catches seams not visible via color differences alone.                      |
| Combine metrics and apply thresholds to decide tileability   | Determine whether the image is seamless along X, Y or both axes.                                             |
| Provide an overlay preview and optional TexTile‑based metric | Improves user understanding and adds a future‑proof AI‑powered metric.                                       |

By following this multi‑scale edge‑comparison strategy and optionally incorporating the TexTile metric, your seamless checker can detect subtle seams more reliably than simple pixel differences. The 2×2 tiling and local discontinuity detection are rooted in state‑of‑the‑art research, ensuring that the checker adheres to modern best practices.
