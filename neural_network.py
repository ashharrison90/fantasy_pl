"""
Create a neural network to analyse the previous data and predict points using PyTorch
"""
from dateutil import parser
from numpy import random, sqrt, stack
from pandas import read_csv
from torch.utils.data import random_split
from torch.nn import BatchNorm1d, Dropout, Embedding, Linear, Module, ModuleList, MSELoss, ReLU, Sequential
from torch.optim import SGD
from constants import DEFAULT_MODEL_PATH
import logging
import os
import torch

logger = logging.getLogger()

class Model(Module):
    def __init__(self, embedding_size, num_numerical_cols):
        super().__init__()
        self.all_embeddings = ModuleList([Embedding(ni, nf) for ni, nf in embedding_size])
        self.embedding_dropout = Dropout(0.1)
        self.batch_norm_num = BatchNorm1d(num_numerical_cols)

        all_layers = []
        num_categorical_cols = sum((nf for ni, nf in embedding_size))
        layer_size = num_categorical_cols + num_numerical_cols

        layer_sizes = [100, 50, 25]
        for i, new_layer_size in enumerate(layer_sizes):
            all_layers.append(Linear(layer_size, new_layer_size))
            all_layers.append(ReLU(inplace=True))
            all_layers.append(BatchNorm1d(new_layer_size))
            all_layers.append(Dropout(0.2))
            layer_size = new_layer_size

        all_layers.append(Linear(layer_sizes[-1], 1))
        self.layers = Sequential(*all_layers)

    def forward(self, x_categorical, x_numerical):
        embeddings = []
        for i, e in enumerate(self.all_embeddings):
            embeddings.append(e(x_categorical[:,i]))
        x = torch.cat(embeddings, 1)
        x = self.embedding_dropout(x)
        x_numerical = self.batch_norm_num(x_numerical)
        x = torch.cat([x, x_numerical], 1)
        x = self.layers(x)
        return x

# prepare and load the data
path = 'https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/cleaned_merged_seasons.csv'
df = read_csv(path, index_col=0, dtype={
    'season_x': 'string',
    'name': 'string',
    'position': 'string',
    'team_x': 'string',
    'assists': int,
    'bonus': int,
    'bps': int,
    'clean_sheets': int,
    'creativity': float,
    'element': int,
    'fixture': int,
    'goals_conceded': int,
    'goals_scored': int,
    'ict_index': float,
    'influence': float,
    'kickoff_time': 'string',
    'minutes': int,
    'opponent_team': int,
    'opp_team_name': 'string',
    'own_goals': int,
    'penalties_missed': int,
    'penalties_saved': int,
    'red_cards': int,
    'round': int,
    'saves': int,
    'selected': int,
    'team_a_score': float,
    'team_h_score': float,
    'threat': float,
    'total_points': int,
    'transfers_balance': int,
    'transfers_in': int,
    'transfers_out': int,
    'value': int,
    'was_home': bool,
    'yellow_cards': int,
    'GW': int
})
# remove all values without any minutes played
df = df[df['minutes'] > 0]
# convert kickoff times to epoch timestamps
df['kickoff_time'] = df['kickoff_time'].apply(lambda x: parser.isoparse(x).timestamp())

# define the columns we're interested in
categorical_columns = ['name', 'opp_team_name', 'position', 'season_x', 'was_home']
numerical_columns = ['kickoff_time', 'round', 'value', 'GW']
outputs = ['total_points']

# set categorical columns to have type=category
# these will be converted into unique integers
# calculate the categorical_embedding_size
for category in categorical_columns:
    df[category] = df[category].astype('category')
categorical_column_sizes = [len(df[column].cat.categories) for column in categorical_columns]
categorical_embedding_sizes = [(col_size, min(50, (col_size+1)//2)) for col_size in categorical_column_sizes]

# split the data 80/20 into training and test data
msk = random.rand(len(df)) < 0.8
training_data = df[msk]
test_data = df[~msk]

# convert data into tensors of the correct format
categorical_training_data = stack([training_data[col].cat.codes.values for col in categorical_columns], 1)
categorical_training_data = torch.tensor(categorical_training_data, dtype=torch.int64)
categorical_test_data = stack([test_data[col].cat.codes.values for col in categorical_columns], 1)
categorical_test_data = torch.tensor(categorical_test_data, dtype=torch.int64)
numerical_training_data = stack([training_data[col].values for col in numerical_columns], 1)
numerical_training_data = torch.tensor(numerical_training_data, dtype=torch.float)
numerical_test_data = stack([test_data[col].values for col in numerical_columns], 1)
numerical_test_data = torch.tensor(numerical_test_data, dtype=torch.float)
training_outputs = torch.tensor(training_data[outputs].values, dtype=torch.float).flatten()
test_outputs = torch.tensor(test_data[outputs].values, dtype=torch.float).flatten()

# define the neural network model
model = Model(categorical_embedding_sizes, len(numerical_columns))

def get_player(player_name):
    name_dict = dict(enumerate(df['name'].cat.categories))
    player_id = None
    for key, value in name_dict.items():
        if value == player_name:
            player_id = key
            break
    return player_id

def get_team(team_name):
    opp_team_name_dict = dict(enumerate(df['opp_team_name'].cat.categories))
    team_id = None
    for key, value in opp_team_name_dict.items():
        if value == team_name:
            team_id = key
            break
    return team_id

def get_position(position):
    position_dict = dict(enumerate(df['position'].cat.categories))
    position_id = None
    for key, value in position_dict.items():
        if value == position:
            position_id = key
            break
    return position_id

def get_was_home(is_home):
    was_home_dict = dict(enumerate(df['was_home'].cat.categories))
    was_home = None
    for key, value in was_home_dict.items():
        if key == is_home:
            was_home = value
            break
    return was_home

def get_season_id(season):
    season_dict = dict(enumerate(df['season_x'].cat.categories))
    season_id = None
    for key, value in season_dict.items():
        if value == season:
            season_id = key
            break
    return season_id

# train the model
def train_model():
    logger.info('Training the model. This could take a long time...')
    model.train()
    # define the optimization
    loss_function = MSELoss()
    optimizer = SGD(model.parameters(), lr=0.001, momentum=0.9)
    epochs = 500
    # enumerate epochs
    for epoch in range(epochs):
        # compute the model output
        predictions = model(categorical_training_data, numerical_training_data).squeeze()
        # calculate loss compared to actual outputs
        loss = loss_function(predictions, training_outputs)
        logger.info('Epoch: {}/{}. Loss: {:.2f}'.format(epoch+1, epochs, loss))
        # clear the gradients
        optimizer.zero_grad()
        # credit assignment
        loss.backward()
        # update model weights
        optimizer.step()

def test_model():
    logger.info('Testing the model...')
    model.eval()
    loss_function = MSELoss()
    with torch.no_grad():
        predictions = model(categorical_test_data, numerical_test_data).squeeze()
        loss = loss_function(predictions, test_outputs)
    logger.info('MSE: %.3f, RMSE: %.3f' % (loss, sqrt(loss)))

def predict_points(player_name, opposition_team_name, position, is_home, season, kickoff_time, round, cost, gameweek):
    """
    Use the model to make a points prediction given the input data.
    """
    model.eval()
    with torch.no_grad():
        player_id = get_player(player_name)
        opposition_team_id = get_team(opposition_team_name)
        position_id = get_position(position)
        was_home = get_was_home(is_home)
        season_id = get_season_id(season)
        categorical_data = torch.tensor([[player_id, opposition_team_id, position_id, season_id, was_home]], dtype=torch.int64)
        numerical_data = torch.tensor([[parser.isoparse(kickoff_time).timestamp(), round, cost, gameweek]], dtype=torch.float)
        return model(categorical_data, numerical_data).squeeze()

def load_model(path=DEFAULT_MODEL_PATH):
    logger.info('Loading model from {}'.format(os.path.join(os.getcwd(), path)))
    model.load_state_dict(torch.load(path))

def save_model(path=DEFAULT_MODEL_PATH):
    logger.info('Saving model to {}'.format(os.path.join(os.getcwd(), path)))
    torch.save(model.state_dict(), path)
