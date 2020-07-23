# Aim 
The aim of the project is to detect Malaria in cell images . The dataset is provided by the National Library of Medicine and contains 13.780 images of paracitized and 13.780 images 
of uninfected cells.


# Model 
A CNN model is developed using Tensorflow. The network consists of three 3x3 convolutions, each followed by a rectified linear unit (ReLU) and a 2x2 max pooling operation with 
stride 2 for downsampling. At each downsampling step we double the number of feature channels. In order to evaluate the performance of our model, we demonstrate the train accuracy, the train loss,
the validation accuracy and the validation loss in the following diagram. After 25 epochs validation accuracy is 92.92%.





# Feature importance
Finally, we aim to invetigate the features which have the biggest impact on predictions using permutation importance from eli5 library. Permutation importance approach is fast to calculate, widely used and understood, and consistent with properties we would want a feature importance measure to have. The results of the analysis are the following:

![image](https://user-images.githubusercontent.com/43147324/86924392-1140a500-c138-11ea-9e4d-ee95f0db7abb.png)

The values towards the top are the most important features, and those towards the bottom are the least significant features.
The number in each row demonstrates how much the performance of the model decreased with a random shuffling of the corresponding column data using the accuracy as the performance metric. ca, thal and cp are the most mportant features and those which influence most the final prediction of the model.


# References
 Kaggle for DataSource
 (https://www.kaggle.com/ronitf/heart-disease-
