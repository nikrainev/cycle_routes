import numpy as np

class UCB:
    def __init__(self, n_arms=None, reward_history=None, t = 0):
        if reward_history is None:
            reward_history = []
            
        self.n_arms = n_arms
        self.reward_history = reward_history
        self.t = t

    # Выбираем номер ручки
    def decide(self):
        # Если есть ручка которую еще не дергали, то выбираем ее
        for arm_id in range(self.n_arms):
            if len(self.reward_history[arm_id]) == 0:
                return arm_id

        # Подсчитываем коэффициенты для всех ручек    
        conf_bounds = [
            # Собственно это формула UCB, с помощью нее расчитываем коэффициент
            np.mean(history) + np.sqrt(2 * np.log(self.t) / len(history))
            for history in self.reward_history
        ]

        # Выбираем ручку с максимальным коэффициентом (так как их может быть несколько, выбираем одну случайным образом)
        return int(np.random.choice(
            np.argwhere(conf_bounds == np.max(conf_bounds)).flatten()
        ))

def exists(it):
    return it is not None

def is_loop_rewards_history(predictions_arr):
    def is_loop(prediction):
        if prediction['isLoop'] and prediction['isUserLike']:
            return 1
        else:
            return 0
            
    return list(filter(exists, list(map(is_loop, predictions_arr))))

def is_not_loop_rewards_history(predictions_arr):
    def is_loop(prediction):
        if not prediction['isLoop'] and prediction['isUserLike']:
            return 1
        else:
            return 0

    return list(filter(exists, list(map(is_loop, predictions_arr))))
    
def short_distance_history(predictions_arr):
    def is_match(prediction):
        if prediction['distance'] < 20000 and prediction['isUserLike']:
            return 1
        elif prediction['distance'] < 20000:
            return 0
        else:
            return None
    return list(filter(exists, list(map(is_match, predictions_arr))))
    
def medium_distance_history(predictions_arr):
    def is_match(prediction):
        if 20000 < prediction['distance'] < 60000 and prediction['isUserLike']:
            return 1
        elif 20000 < prediction['distance'] < 60000:
            return 0
        else:
            return None
    return list(filter(exists, list(map(is_match, predictions_arr))))

def long_distance_history(predictions_arr):
    def is_match(prediction):
        if 60000 < prediction['distance'] < 100000 and prediction['isUserLike']:
            return 1
        elif 60000 < prediction['distance'] < 100000:
            return 0
        else:
            return None
    return list(filter(exists, list(map(is_match, predictions_arr))))

def ultra_long_distance_history(predictions_arr):
    def is_match(prediction):
        if 100000 < prediction['distance'] and prediction['isUserLike']:
            return 1
        elif 100000 < prediction['distance']:
            return 0
        else:
            return None
    return list(filter(exists, list(map(is_match, predictions_arr))))

def get_user_next_prediction(db, chat_id):
    current_predictions = db.get_user_predictions(chat_id)
    distance_history = [
        short_distance_history(current_predictions),
        medium_distance_history(current_predictions),
        long_distance_history(current_predictions),
        ultra_long_distance_history(current_predictions)
    ]

    is_loop_history = [
        is_loop_rewards_history(current_predictions),
        is_not_loop_rewards_history(current_predictions),
    ]
    
    duration_UCB = UCB(n_arms=4, reward_history=distance_history, t = len(current_predictions))
    is_loop_UCB = UCB(n_arms=2, reward_history=is_loop_history, t = len(current_predictions))
    
    duration_decide = duration_UCB.decide()
    is_loop_decide = is_loop_UCB.decide()

    min_distance = 0
    max_distance = 0

    if duration_decide == 0:
        min_distance = 0
        max_distance = 20000
    elif duration_decide == 1:
        min_distance = 20000
        max_distance = 60000
    elif duration_decide == 2:
        min_distance = 60000
        max_distance = 100000
    else:
        min_distance = 100000
        max_distance = 1000000

    return {
        'distanceRange': {
            'min': min_distance,
            'max': max_distance,
        },
        'isLoop': is_loop_decide == 0
    }
