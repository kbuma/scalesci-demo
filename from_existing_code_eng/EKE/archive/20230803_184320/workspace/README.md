To convert the code into a Jupyter notebook, we will create a single notebook file that includes all the code from the original files. We will organize the code into cells to make it more interactive and easier to run.

Here's the breakdown of the core classes, functions, and methods that will be necessary:

1. `lat_lon()`: A function to get the map projection and the lat and lon values from the WRF data.
2. `butter_bandpass_filter()`: A function to filter variables for waves with periods between 3-5 days using a Butterworth bandpass filter.
3. `plot_eke()`: A function to generate the plot for the EKE distribution.
4. `main()`: The main function that performs the computation and generates the plot.

Now, let's proceed with the implementation of the Jupyter notebook.

**wrf_eke_nersc_ex.ipynb**

