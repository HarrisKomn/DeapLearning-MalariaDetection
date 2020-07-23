# Aim 
The aim of the project is to detect Malaria in cell images . The dataset is provided by the National Library of Medicine and contains 13.780 images of paracitized and 13.780 images 
of uninfected cells.


# Model 
A CNN model is developed using Tensorflow. The network consists of three 3x3 convolutions, each followed by a rectified linear unit (ReLU) and a 2x2 max pooling operation with 
stride 2 for downsampling. At each downsampling step we double the number of feature channels. The Convolutions are followed by 3 Dense layers at the final stage of the newtork. In order to evaluate the performance of our model, we demonstrate the train accuracy, the train loss,
the validation accuracy and the validation loss in the following diagram. After 25 epochs validation accuracy is 92.92%.


![image](https://user-images.githubusercontent.com/43147324/88307797-029be580-cd15-11ea-8fa3-42168d884612.png)




# References
 National Library of Medicine
 (https://lhncbc.nlm.nih.gov/publication/pub9932)
