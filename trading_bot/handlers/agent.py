import random

from collections import deque

import numpy as np
import tensorflow as tf
import keras.backend as K

from keras.models import Sequential
from keras.models import load_model, clone_model
from keras.layers import Input, Dense, Flatten, Conv1D, MaxPooling1D, Bidirectional, Dropout, GlobalAveragePooling1D#, LSTM
# from kerasbeats import NBeatsModel
# from keras.optimizers import Adam
import tensorflow.keras.optimizers as tfl
# from .transformer import Transformer
from keras.models import Model


def softmax(x):
    exp_x = np.exp(x)
    return exp_x / np.sum(exp_x, axis=0, keepdims=True)


def huber_loss(y_true, y_pred, clip_delta=1.0):
    """Huber loss - Custom Loss Function for Q Learning

    Links: 	https://en.wikipedia.org/wiki/Huber_loss
            https://jaromiru.com/2017/05/27/on-using-huber-loss-in-deep-q-learning/
    """
    error = y_true - y_pred
    cond = K.abs(error) <= clip_delta
    squared_loss = 0.5 * K.square(error)
    quadratic_loss = 0.5 * K.square(clip_delta) + clip_delta * (K.abs(error) - clip_delta)
    return K.mean(tf.where(cond, squared_loss, quadratic_loss))



def gaussian_mean(x, mu, sigma):
    return np.exp(-0.5 * ((x - mu) / sigma) ** 2)

def convert_to_array(number):
    x = np.arange(0, 10)
    mean_array = []

    # Calculate the Gaussian distribution centered at the given number
    gaussian_dist = gaussian_mean(x, number, 1.0)

    # Calculate the mean of the y values within the specified ranges
    mean_array.append(np.mean(gaussian_dist[4:7]))  # 4-6 hold
    mean_array.append(np.mean(gaussian_dist[0:4]))  # 0-3 sell
    mean_array.append(np.mean(gaussian_dist[7:10]))  # 7-9 buy

    return mean_array



class Agent:
    """ Stock Trading Bot """

    def __init__(self, state_size, strategy="t-dqn", reset_every=1000, pretrained=False, model_name=None, balance=1000.):
        self.strategy = strategy

        # agent config
        self.state_size = state_size    	# normalized previous days
        self.action_size = 3           		# [sit, buy, sell]
        self.model_name = model_name
        self.inventory = []
        self.memory = deque(maxlen=10000)
        self.first_iter = True

        # model config
        self.model_name = model_name
        self.gamma = 0.95 # affinity for long term reward
        self.epsilon = 1.0
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learning_rate = 0.001
        self.loss = huber_loss
        self.custom_objects = {"huber_loss": huber_loss}  # important for loading the model from memory
        self.optimizer = tfl.Adam(learning_rate=self.learning_rate)
        self.balance = balance

        if pretrained and self.model_name is not None:
            self.model = self.load()
        elif "transformer" in self.model_name:
            self.model = self.transformer()
            print("Transformer as backbone")
        else:
            self.model = self._model()

        # strategy config
        if self.strategy in ["t-dqn", "double-dqn"]:
            self.n_iter = 1
            self.reset_every = reset_every

            # target network
            self.target_model = clone_model(self.model)
            self.target_model.set_weights(self.model.get_weights())
            # self.target_model = self.model

    def _model(self):
        """Creates the model
        """
        model = Sequential()
        model.add(Dense(units=128, activation="relu", input_dim=self.state_size))
        model.add(Dense(units=256, activation="relu"))
        model.add(Dense(units=256, activation="relu"))
        model.add(Dense(units=128, activation="relu"))
        model.add(Dense(units=self.action_size, activation="softmax"))

        model.compile(loss=self.loss, optimizer=self.optimizer)
        return model

    # def _model(self):
    #     """Creates the model
    #     """
    #     nbeats = NBeatsModel(lookback=10)
    #     nbeats.build_layer()
    #     nbeats.build_model()
    #     nbeats.model.compile(loss = 'mse', optimizer = tf.keras.optimizers.RMSprop(0.001))
    #     return nbeats

    def transformer(self):
        model = self._transformer()

        # model.load_weights("Transformer_AAPL.h5", by_name=True)

        # for layer in model.layers:
        #     if layer.name != "new_proj":
        #         layer.trainable = False

        for layer in model.layers:
            print(layer.name, layer.trainable)
        # model.add(Dense(units=128, activation="relu", input_dim=self.state_size))
        # model.add(Dense(units=256, activation="relu"))
        # model.add(Dense(units=256, activation="relu"))
        # model.add(Dense(units=128, activation="relu"))
        # model.add(Dense(units=self.action_size))

        model.compile(loss=self.loss, optimizer=self.optimizer)
        return model

    def _transformer(self):
        # print(self.state_size)
        X_input = Input((self.state_size, 1))
        # x = Dense(units=128, activation="relu")(X_input)
        # print("input", X_input.shape)



        tr = Transformer()
        x = Dense(32, activation="relu")(X_input)

        # x = Conv1D(filters=32, kernel_size=3, padding="same", activation="relu")(X_input)
        # print("x", x.shape)

        # x = MaxPooling1D(pool_size=2)(X)
        # x= Conv1D(filters=64, kernel_size=3, padding="same", activation="tanh")(X)
        # x = MaxPooling1D(pool_size=2)(X)

        for _ in range(tr.num_transformer_blocks):
            x = tr.transformer_encoder(x)
        # print("1",x.shape)
        # x = MaxPooling1D(pool_size=2)(x)
        # x = Conv1D(filters=16, kernel_size=3, padding="same", activation="tanh")(x)
        # x = MaxPooling1D(pool_size=2)(x)
        # x = Flatten()(x)
        x = GlobalAveragePooling1D(data_format="channels_first")(x)
        # print("1",x.shape)
        for dim in tr.mlp_units:
            x = Dense(dim, activation="relu")(x)
            x = Dropout(tr.mlp_dropout)(x)
        x = Dense(64, activation="relu")(x)
        x = Dense(32, activation="relu")(x)
        x = Dense(16, activation="relu")(x)
        x = Dense(units=self.action_size, name="new_proj")(x)

        return Model(inputs=X_input, outputs = x)

    def remember(self, state, action, reward, next_state, done):
        """Adds relevant data to memory
        """
        self.memory.append((state, action, reward, next_state, done))

    def act(self, state, is_eval=False):
        """Take action from given possible set of actions
        """
        # take random action in order to diversify experience at the beginning
        if not is_eval and random.random() <= self.epsilon:
            return random.randrange(self.action_size)

        if self.first_iter:
            self.first_iter = False
            return 1, 0.33 # make a definite buy on the first iter

        action_probs = self.model.predict(state, verbose=0)
        action = np.argmax(action_probs[0])
        return action, action_probs[:,action].item()

    def act_with_score(self, state, scores, is_eval=False):
        """Take action from given possible set of actions
        """

        # print("$$", state, scores)
        # Test case with number = 8
        print("score", scores)
        scores_dist = convert_to_array(scores.mean())
        scores_dist = softmax(scores_dist)
        # print("score", scores.mean(), "| Gaussian Dist:", scores_dist)



        # take random action in order to diversify experience at the beginning
        if not is_eval and random.random() <= self.epsilon:
            return random.randrange(self.action_size)

        if self.first_iter:
            self.first_iter = False
            return 1, 0.33 # make a definite buy on the first iter

        action_probs = self.model.predict(state, verbose=0)
        print("Action probs:", action_probs)

        action = np.argmax(action_probs[0] * scores_dist)
        # print("Action before:", np.argmax(action_probs[0]), "| after:", action)
        return action, action_probs[:,action].item()

    def train_experience_replay(self, batch_size):
        """Train on previous experiences in memory
        """
        mini_batch = random.sample(self.memory, batch_size)
        X_train, y_train = [], []
        
        # DQN
        if self.strategy == "dqn":
            for state, action, reward, next_state, done in mini_batch:
                if done:
                    target = reward
                else:
                    # approximate deep q-learning equation
                    target = reward + self.gamma * np.amax(self.model.predict(next_state, verbose=0)[0])

                # estimate q-values based on current state
                q_values = self.model.predict(state, verbose=0)
                # update the target for current action based on discounted reward
                q_values[0][action] = target

                X_train.append(state[0])
                y_train.append(q_values[0])

        # DQN with fixed targets
        elif self.strategy == "t-dqn":
            if self.n_iter % self.reset_every == 0:
                # reset target model weights
                self.target_model.set_weights(self.model.get_weights())

            for state, action, reward, next_state, done in mini_batch:
                if done:
                    target = reward
                else:
                    # approximate deep q-learning equation with fixed targets
                    # print(self.target_model.predict(next_state, verbose=0))
                    target = reward + self.gamma * np.amax(self.target_model.predict(next_state, verbose=0)[0])

                # estimate q-values based on current state
                q_values = self.model.predict(state, verbose=0)
                # update the target for current action based on discounted reward
                q_values[0][action] = target

                X_train.append(state[0])
                y_train.append(q_values[0])

        # Double DQN
        elif self.strategy == "double-dqn":
            if self.n_iter % self.reset_every == 0:
                # reset target model weights
                self.target_model.set_weights(self.model.get_weights())

            for state, action, reward, next_state, done in mini_batch:
                if done:
                    target = reward
                else:
                    # approximate double deep q-learning equation
                    target = reward + self.gamma * self.target_model.predict(next_state, verbose=0)[0][np.argmax(self.model.predict(next_state, verbose=0)[0])]

                # estimate q-values based on current state
                q_values = self.model.predict(state, verbose=0)
                # update the target for current action based on discounted reward
                q_values[0][action] = target

                X_train.append(state[0])
                y_train.append(q_values[0])
                

        else:
            raise NotImplementedError()

        # update q-function parameters based on huber loss gradient
        loss = self.model.fit(
            np.array(X_train), np.array(y_train), epochs=1, verbose=0).history["loss"][0]

        # as the training goes on we want the agent to
        # make less random and more optimal decisions
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
        # print("NoNoNoYes")
        return loss

    def save(self, episode):
        self.model.save("models/{}_{}.h5".format(self.model_name, episode))

    def load(self):
        return load_model(self.model_name, custom_objects=self.custom_objects)
