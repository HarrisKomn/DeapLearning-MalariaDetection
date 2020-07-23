import numpy as np
import cv2
import os
import matplotlib.pyplot as plt
from PIL import Image
from keras.models import Sequential, load_model
from keras.layers import Dense, Dropout, Flatten, Conv2D, MaxPool2D, BatchNormalization
from sklearn.model_selection import train_test_split
from keras.utils import to_categorical

np.random.seed(1000)

# Resize Images
image_directory= 'cell_images/cell_images_small/'
SIZE=64
x_images=[]
label=[]

parasitized_images=os.listdir(image_directory+ 'Parasitized/')
for i,image_name in enumerate(parasitized_images):
    if(image_name.split('.')[1]=='png'):
        image=cv2.imread(image_directory+'Parasitized/'+image_name)
        image=Image.fromarray(image,'RGB')
        image=image.resize((SIZE,SIZE))
        x_images.append(np.array(image))
        label.append(0)

uninfected_images=os.listdir(image_directory+ 'Uninfected/')
for i,image_name in enumerate(uninfected_images):
    if(image_name.split('.')[1]=='png'):
        image=cv2.imread(image_directory+'Uninfected/'+image_name)
        image=Image.fromarray(image,'RGB')
        image=image.resize((SIZE,SIZE))
        x_images.append(np.array(image))
        label.append(1)


# Create the Model
model=Sequential()
model.add(Conv2D(32,(3,3),input_shape=(64,64,3),padding='same',activation = 'relu'))
model.add(MaxPool2D(pool_size=(2,2)))
model.add(BatchNormalization())
model.add(Dropout(0.2))


model.add(Conv2D(64,(3,3),padding='same',activation = 'relu'))
model.add(MaxPool2D(pool_size=(2,2)))
model.add(BatchNormalization())
model.add(Dropout(0.2))

model.add(Conv2D(128,(3,3),padding='same',activation = 'relu'))
model.add(MaxPool2D(pool_size=(2,2)))
model.add(BatchNormalization())
model.add(Dropout(0.2))

model.add(Flatten())
model.add(Dense(512,activation='relu'))
model.add(BatchNormalization())
model.add(Dropout(0.2))
model.add(Dense(256,activation='relu'))
model.add(BatchNormalization())
model.add(Dropout(0.2))
model.add(Dense(2,activation='sigmoid'))

model.summary()
model.compile(optimizer='Adam', loss='categorical_crossentropy', metrics=['accuracy'])


# Split the train set
X_train, X_test, y_train, y_test = train_test_split(x_images,to_categorical(np.array(label)),test_size=0.20,random_state=0)



#for x, y in  zip(X_test, y_test):
#    plt.imshow(x)
#    plt.show()
#    print (y)

# Training and Save Model

history=model.fit(np.array(X_train),y_train, batch_size=64,verbose=1,epochs=25,  validation_data=(np.array(X_test), y_test))
model.save('malaria_cnn.h5')
print("Test_Accuracy: {:.2f}%".format(model.evaluate(np.array(X_test), np.array(y_test))[1]*100))

score = model.evaluate(np.array(X_test), np.array(y_test))
print('Test loss:', score[0])
print('Test accuracy:', score[1])

f, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
t = f.suptitle('CNN Performance', fontsize=12)
f.subplots_adjust(top=0.85, wspace=0.3)

# summarize history for accuracy
max_epoch = len(history.history['accuracy'])+1
epoch_list = list(range(1,max_epoch))
ax1.plot(epoch_list, history.history['accuracy'], label='Train Accuracy')
ax1.plot(epoch_list, history.history['val_accuracy'], label='Validation Accuracy')
ax1.set_xticks(np.arange(1, max_epoch, 5))
ax1.set_ylabel('Accuracy Value')
ax1.set_xlabel('Epoch')
ax1.set_title('Accuracy')
l1 = ax1.legend(loc="best")

# summarize history for loss
ax2.plot(epoch_list, history.history['loss'], label='Train Loss')
ax2.plot(epoch_list, history.history['val_loss'], label='Validation Loss')
ax2.set_xticks(np.arange(1, max_epoch, 5))
ax2.set_ylabel('Loss Value')
ax2.set_xlabel('Epoch')
ax2.set_title('Loss')
l2 = ax2.legend(loc="best")


plt.show()
