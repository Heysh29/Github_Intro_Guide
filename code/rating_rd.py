import pandas as pd
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt

# Sample data loading for New York listings
all_data = pd.read_csv('data/middle/Boston_listing.csv')

# Ensure 'price' is a float and remove any non-numeric characters like dollar signs
all_data['price'] = all_data['price'].replace('[\$,]', '', regex=True).astype(float)

# Change the dependent variable to the log of 'number_of_reviews'
all_data['log_new_review'] = np.log(all_data['new_review'] + 1)

dependent_var = 'new_review'  # Now using log of the original dependent variable

# Define a kernel function for weights, triangular kernel as an example
def triangular_kernel(x, bandwidth):
    return np.maximum(1 - np.abs(x) / bandwidth, 0) # You can change this to 'price' or any other variable as needed

# Filter data to keep only observations close to the thresholds
thresholds = [4]
bandwidth = 0.02  # adjust the bandwidth as needed

# Run the regression for each threshold
for threshold in thresholds:
    data_threshold = all_data[(all_data['review_scores_rating'] >= threshold - bandwidth) &
                              (all_data['review_scores_rating'] <= threshold + bandwidth)].copy()

    data_threshold['above_threshold'] = (data_threshold['review_scores_rating'] > threshold).astype(int)

    # Calculate the distance from the threshold for each observation
    data_threshold['distance'] = data_threshold['review_scores_rating'] - threshold

    # Apply the kernel function to get weights
    data_threshold['weights'] = triangular_kernel(data_threshold['distance'], bandwidth)

    # Check if there are enough observations on both sides of the threshold
    if len(data_threshold[data_threshold['above_threshold'] == 0]) > 0 and len(
            data_threshold[data_threshold['above_threshold'] == 1]) > 0:
        # Run the weighted regression including 'price' as a control variable
        X = data_threshold[['review_scores_rating', 'above_threshold', 'price']]
        X = sm.add_constant(X)
        y = data_threshold[dependent_var]
        weights = data_threshold['weights']
        model = sm.WLS(y, X, weights=weights).fit()

        # Get the RD estimate and its standard error
        rd_estimate = model.params['above_threshold']
        rd_se = model.bse['above_threshold']
        print(f'Threshold {threshold}: RD Estimate = {rd_estimate}, Standard Error = {rd_se}')

        # Generate predictions for plotting
        x_plot = np.linspace(threshold - bandwidth, threshold + bandwidth, 100)
        mean_price = data_threshold['price'].mean()
        # Calculate the mean price for the control variable

        # Create the above threshold binary indicator for the prediction data
        above_threshold_plot = (x_plot > threshold).astype(int)

        # Stack the x_plot, above_threshold_plot, and mean_price into x_plot_with_constant
        # You should have a column for the intercept (constant), review_scores_rating, above_threshold, and price
        x_plot_with_constant = sm.add_constant(np.column_stack((x_plot, above_threshold_plot)))
        # Add a column with the mean price for the prediction
        x_plot_with_constant = np.insert(x_plot_with_constant, x_plot_with_constant.shape[1], mean_price, axis=1)

        # Ensure the shape of x_plot_with_constant matches the number of parameters in the model
        if x_plot_with_constant.shape[1] != len(model.params):
            raise ValueError(
                f"The shape of x_plot_with_constant {x_plot_with_constant.shape} does not match the number of parameters in the model {len(model.params)}.")

        # If the shapes match, make predictions
        y_plot = model.predict(x_plot_with_constant)

        # Plot the results
        plt.figure()
        plt.scatter(data_threshold['review_scores_rating'], data_threshold[dependent_var], color='grey', alpha=0.5)
        plt.plot(x_plot, y_plot, color='blue', label='Fitted Line')
        plt.axvline(x=threshold, color='black', linestyle='--')
        plt.xlabel('Review Scores Rating')
        plt.ylabel(dependent_var.replace('_', ' ').title())
        plt.title(f'Regression Discontinuity at Threshold {threshold}')

        # Print the RD estimate and SE on the graph
        plt.text(threshold, max(y_plot) * 0.9, f'RD Estimate = {rd_estimate:.3f}\nSE = {rd_se:.3f}', fontsize=9)

        plt.legend()
        plt.savefig(f'output/figure/rating_rd_{threshold}_Boston.png', bbox_inches='tight')