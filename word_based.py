
# coding: utf-8

# In[1]:


import numpy, sys, pandas as pd
from random import randint
from pickle import dump, load
from keras.models import Sequential, load_model
from keras.layers import Dense
from keras.layers import Dropout
from keras.layers import LSTM
from keras.callbacks import ModelCheckpoint
from keras.utils import np_utils
from keras.preprocessing.text import Tokenizer
from keras.utils import to_categorical
from keras.layers import Embedding, Flatten
from keras.preprocessing.sequence import pad_sequences


# In[2]:


# load doc into memory
def load_doc(filename):
    # open the file as read only
    file = open(filename, 'r')
    # read all text
    text = file.read()
    # close the file
    file.close()
    tokens = text.split()
    print(tokens[:100])
    print('Total Tokens: %d' % len(tokens))
    print('Unique Tokens: %d' % len(set(tokens)))
    return tokens


# In[3]:




# organize into sequences of tokens
#the plus one is because the last val in the list will be the expected prediction. 
#Its our Y-train
def sequencesCreate(length, tokens):
    sequences = list()
    for i in range(length, len(tokens)):
        # select sequence of tokens
        seq = tokens[i-length:i]
        # convert into a line
        #line = ' '.join(seq)
        # store
        sequences.append(seq)
    print('Total Sequences: %d' % len(sequences))
    print(f'sequences: {type(sequences[0])}')
    
    tokenizer = Tokenizer()
    # integer encode sequences of words
    #sequences = [str(i) for i in sequences]
    # print(f'tokenizer: {tokenizer}')
    tokenizer.fit_on_texts(sequences)
    # print(f'tokenizer: {tokenizer}')
    sequences = tokenizer.texts_to_sequences(sequences)
    # print(f'sequences: {sequences}')
    
    return sequences, tokenizer


# In[4]:


# define model
def defineModel(vocab_size, seq_length, modelList, length):
    model = Sequential()
    print(f'model.add(Embedding({vocab_size}, {seq_length}, input_length={seq_length}))')
    for layer in modelList:
        if layer[0] == 'Embedding': 
            (_, i2, i3) = layer
            model.add(Embedding(i2, i3, input_length=i3))
        if layer[0] == 'LSTM':
            #model.add(LSTM(100, return_sequences=True))
            (_, neurons, rsequences) = layer
            model.add(LSTM(neurons, return_sequences=rsequences))
            print(f'model.add(LSTM({neurons}, return_sequences={rsequences}))')

        if layer[0] == 'Dropout':
            #model.add(Dropout(0.2))
            (_, dropout_rate, _) = layer
            model.add(Dropout(dropout_rate))
            print(f'model.add(Dropout({dropout_rate}))')

        if layer[0] == 'Dense':
            #model.add(Dense(100, activation='relu'))
            (_, neurons, afunction) = layer
            model.add(Dense(neurons, activation=afunction))
            print(f'model.add(Dense({neurons}, activation={afunction}))')

        if layer[0] == 'Flatten':
            model.add(Flatten())
            print(f'model.add(Flatten())')
        
    #Create the model name
    modelName = f'{length}'
    for layer in modelList:
        modelName+= f'_{layer[0]}_{layer[1]}_{layer[2]}'

    #model.add(LSTM(100, return_sequences=True))
    #model.add(Dropout(0.2))
    #model.add(LSTM(100))
    #model.add(Dense(100, activation='relu'))
    #model.add(Dense(vocab_size, activation='softmax'))
    print(model.summary())
    return model, modelName


# In[5]:


def modelFit(model, modelName, X, y, seq_length, batch_size, epochs):
    # compile model
    model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

    # define the checkpoint
    filepath=f"wi_{{epoch:02d}}_{{loss:.4f}}__{modelName}.hdf5"
    checkpoint = ModelCheckpoint(filepath, monitor='loss', verbose=1, save_best_only=True, mode='min')
    callbacks_list = [checkpoint]

    # fit model
    history_callback = model.fit(X, y, batch_size=batch_size, epochs=epochs, callbacks=callbacks_list)
    return history_callback


# In[6]:


#--- --- ---- --- ---- --- ---- ---- --- ----- ---- ---
# -- Write Files ---- ---- ---- --- ---- --- --- --- -- 
#--- --- ---- --- ---- --- ---- ---- --- ----- ---- ---
def writeFiles(modelName, history_callback):
    loss_history = history_callback.history
    
    # save the model to file
    model.save('m_' + modelName + '.h5')

    # save losses
    with open('h_' + modelName + '.txt', 'w+') as f:
        f.write(str(loss_history))


# In[7]:


# select a seed text
# seed_text = lines[randint(0,len(lines))]
seed_text = '''Whosever room this is should be ashamed!
His underwear is hanging on the lamp.
His raincoat is there in the overstuffed chair,
And the chair is becoming quite mucky and damp.
His workbook is wedged in the window,
His sweater's been thrown on the floor.
His scarf and one ski are'''

print(seed_text + '\n')


# In[8]:


# generate a sequence from a language model
#def generate_seq(model, tokenizer, seq_length, seed_text, n_words):
def generate_seq(model, tokenizer, seq_length, seed_text, n_words):
    # load the model
    model = load_model(model)

    # load the tokenizer
    tokenizer = load(open(tokenizerName, 'rb'))
    
    #Make 50 words long
    seed_text = ' '.join(seed_text.split(' ')[0:seq_length])
    
    result = list()
    in_text = seed_text
    # generate a fixed number of words
    for _ in range(n_words):
        # encode the text as integer
        encoded = tokenizer.texts_to_sequences([in_text])[0]
        # truncate sequences to a fixed length
        encoded = pad_sequences([encoded], maxlen=seq_length, truncating='pre')
        # predict probabilities for each word
        yhat = model.predict_classes(encoded, verbose=0)
        # map predicted word index to word
        out_word = ''
        for word, index in tokenizer.word_index.items():
            if index == yhat:
                out_word = word
                break
        # append to input
        in_text += ' ' + out_word
        result.append(out_word)
    return ' '.join(result)


# In[9]:


def trainModelComplete():
    # -- PARAMETERS -- ---- --- ---- --- --- ---- --- ---- --- ---- --- ---- ---
    #-- ---- ---- --- ---- ----- ---- ----- ---- ----- ----- ---- ---- ---- ----
    #--- PARAMETERS --- --- --- ---- --- --- ---- ---- --- ----- --- --- ----
    #--- --- ---- --- --- --- --- ---- --- --- --- ----- ---- ---- ---- ---- -
    drseuss_text = 'data/combinedText.txt'
    seed_length = 50
    length = seed_length + 1
    epochs = 2
    batch_size = 128
    #--- --- ---- --- --- --- --- ---- --- --- --- ----- ---- ---- ---- ---- -
    #--- --- ---- --- --- --- --- ---- --- --- --- ----- ---- ---- ---- ---- -

    #notes from website:
    #-- Common values are 50, 100, and 300. We will use 50 here, --
    #-- but consider testing smaller or larger values. --
    #-- We will use a two LSTM hidden layers with 100 memory cells each. --
    #-- More memory cells and a deeper network may achieve better results. --
    #-- ---- ---- --- ---- ----- ---- ----- ---- ----- ----- ---- ---- ---- ----
    #-- ---- ---- --- ---- ----- ---- ----- ---- ----- ----- ---- ---- ---- ----
    
    # load document
    drseuss_text = 'data/combinedText.txt'
    tokens = load_doc(drseuss_text)

    sequences, tokenizer = sequencesCreate(length, tokens)
    vocab_size = len(tokenizer.word_index) + 1
    df = pd.DataFrame(sequences)
    X, y = df.iloc[:,:-1], df.iloc[:,-1]
    #One hot encoding
    y = to_categorical(y, num_classes=vocab_size)
    seq_length = X.shape[1]
    print(f'seq_length: {seq_length}\nshape of X: {X.shape}\nshape of y: {y.shape}')
    print(y[0])
    

    modelList = [('Embedding', vocab_size, seq_length), ('LSTM',256,'True'), ('Dense',256,'relu'), ('Dropout',.2,''), 
                 ('LSTM',128,'True'), ('Dense',128,'relu'), ('Dropout',.2,''), 
                 ('LSTM', 64,'False'), ('Dense',64,'relu'), 
                 ('Flatten','',''),('Dense',vocab_size,'softmax')]
    print(f'drseuss_text: \'{drseuss_text}\'\nseed_length: {seed_length}\nepochs: {epochs}\nbatch_size: {batch_size}'
     f'\nmodelList: {modelList}')
    #oneThing = defineModel(vocab_size, seq_length, modelList)
    #print(oneThing)
    model, modelName = defineModel(vocab_size, seq_length, modelList, length)
    #create tokenizer file name .pkl
    tokenizerName = 'toke_' + modelName + '.pkl'
    # save the tokenizer
    dump(tokenizer, open(tokenizerName, 'wb'))
    
    
    history_callback = modelFit(model, modelName, X, y, seq_length, batch_size, epochs)
    writeFiles(modelName, history_callback)


# In[10]:


model = 'm_51_LSTM_256_True_Dense_256_relu_Dropout_0.2__LSTM_128_True_Dense_128_relu_Dropout_0.2__LSTM_64_False_Dense_64_relu_Flatten___Dense_2830_softmax.h5'
tokenizer = 'toke_51_LSTM_256_True_Dense_256_relu_Dropout_0.2__LSTM_128_True_Dense_128_relu_Dropout_0.2__LSTM_64_False_Dense_64_relu_Flatten___Dense_2830_softmax.pkl'

# generate new text
# generated = generate_seq(model, tokenizer, seq_length, seed_text, seed_length)
# print(generated)


# In[11]:


if __name__ == '__main__':
    trainModelComplete()


# In[ ]:


#trainModelComplete()

