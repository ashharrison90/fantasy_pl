# pytorch mlp for regression
from dateutil import parser
from numpy import sqrt, stack, vstack
from math import isnan
from pandas import read_csv
import torch
from torch.utils.data import Dataset, DataLoader, random_split
from torch import int64, Tensor
from torch.nn import BatchNorm1d, ELU, Dropout, Embedding, Hardshrink, Linear, Module, ModuleList, MSELoss, ReLU, Sequential, Sigmoid
from torch.nn.init import xavier_uniform_
from torch.optim import SGD

class Model(Module):
    def __init__(self, embedding_size, num_numerical_cols):
        super().__init__()
        self.all_embeddings = ModuleList([Embedding(ni, nf) for ni, nf in embedding_size])
        self.embedding_dropout = Dropout(0.01)
        self.batch_norm_num = BatchNorm1d(num_numerical_cols)

        all_layers = []
        num_categorical_cols = sum((nf for ni, nf in embedding_size))
        layer_size = num_categorical_cols + num_numerical_cols

        layer_sizes = [1000, 500, 250]
        for i, new_layer_size in enumerate(layer_sizes):
            all_layers.append(Linear(layer_size, new_layer_size))
            all_layers.append(ReLU(inplace=True))
            all_layers.append(BatchNorm1d(new_layer_size))
            all_layers.append(Dropout(0.01))
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

# train the model
def train_model(categorical_train_data, numerical_train_data, model, train_outputs):
    # define the optimization
    loss_function = MSELoss()
    optimizer = SGD(model.parameters(), lr=0.01, momentum=0.9)
    epochs = 100
    # enumerate epochs
    for epoch in range(epochs):
        # compute the model output
        predictions = model(categorical_train_data, numerical_train_data).squeeze()
        # calculate loss compared to actual outputs
        loss = loss_function(predictions, train_outputs)
        print(loss)
        # clear the gradients
        optimizer.zero_grad()
        # credit assignment
        loss.backward()
        # update model weights
        optimizer.step()

def test_model(categorical_test_data, numerical_test_data, model, test_outputs):
    loss_function = MSELoss()
    with torch.no_grad():
        predictions = model(categorical_test_data, numerical_test_data).squeeze()
        loss = loss_function(predictions, test_outputs)
    print('MSE: %.3f, RMSE: %.3f' % (loss, sqrt(loss)))

def predict_points(categorical_data, numerical_data, model):
    """
    Make a points prediction for a row of data given the model.
    """
    print(categorical_data)
    print(numerical_data)
    return model(categorical_data, numerical_data).squeeze()

def get_model():
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
    # convert seasons to integers, e.g. '2019-2020' becomes 2019
    df['season_x'] = df['season_x'].apply(lambda x: int(x.split('-')[0]))

    # define the columns we're interested in
    categorical_columns = ['name', 'opp_team_name', 'position', 'was_home']
    numerical_columns = ['season_x', 'kickoff_time', 'round', 'value', 'GW']
    outputs = ['total_points']

    # set categorical columns to have type=category
    # these will be converted into unique integers
    # calculate the categorical_embedding_size
    for category in categorical_columns:
        df[category] = df[category].astype('category')
    categorical_column_sizes = [len(df[column].cat.categories) for column in categorical_columns]
    categorical_embedding_sizes = [(col_size, min(50, (col_size+1)//2)) for col_size in categorical_column_sizes]

    # convert data into tensors of the correct format
    categorical_data = stack([df[col].cat.codes.values for col in categorical_columns], 1)
    categorical_data = torch.tensor(categorical_data, dtype=torch.int64)
    numerical_data = stack([df[col].values for col in numerical_columns], 1)
    numerical_data = torch.tensor(numerical_data, dtype=torch.float)
    outputs = torch.tensor(df[outputs].values, dtype=torch.float).flatten()

    # print(dict(enumerate(df['name'].cat.categories)))

    # split the data into training and test data
    total_records = len(df)
    test_records = int(total_records * .2)

    categorical_train_data = categorical_data[:total_records-test_records]
    categorical_test_data = categorical_data[total_records-test_records:total_records]
    numerical_train_data = numerical_data[:total_records-test_records]
    numerical_test_data = numerical_data[total_records-test_records:total_records]
    train_outputs = outputs[:total_records-test_records]
    test_outputs = outputs[total_records-test_records:total_records]

    # define the neural network model
    model = Model(categorical_embedding_sizes, numerical_data.shape[1])
    print(model)

    # train the model
    train_model(categorical_train_data, numerical_train_data, model, train_outputs)

    # test the model
    test_model(categorical_test_data, numerical_test_data, model, test_outputs)

    # return the model
    return df, model

# get_model()