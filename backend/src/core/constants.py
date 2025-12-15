import datetime

HORARIOS = {
        "manha": {
            "A": (datetime.time(7, 30), datetime.time(8, 20)),
            "B": (datetime.time(8, 20), datetime.time(9, 10)),
            "C": (datetime.time(9, 30), datetime.time(10, 20)),
            "D": (datetime.time(10, 20), datetime.time(11, 0)),
            "E": (datetime.time(11, 0), datetime.time(11, 50)),
        },
        "tarde": {
            "A": (datetime.time(13, 30), datetime.time(14, 20)),
            "B": (datetime.time(14, 20), datetime.time(15, 10)),
            "C": (datetime.time(15, 30), datetime.time(16, 20)),
            "D": (datetime.time(16, 20), datetime.time(17, 00)),
            "E": (datetime.time(17, 00), datetime.time(17, 50)),
        },
        "noite": {
            "A": (datetime.time(18, 30), datetime.time(19, 20)),
            "B": (datetime.time(19, 20), datetime.time(20, 10)),
            "C": (datetime.time(20, 30), datetime.time(21, 20)),
            "D": (datetime.time(21, 20), datetime.time(22, 00)), # ajuste conforme suas regras
        }
    }

DIAS_MAP = {
        "2": 0,  # Segunda
        "3": 1,  # Terça
        "4": 2,  # Quarta
        "5": 3,  # Quinta
        "6": 4,  # Sexta
        "7": 5,  # Sábado
    }

NUM_PARA_DIA = {
    "2": "SEG",
    "3": "TER",
    "4": "QUA",
    "5": "QUI",
    "6": "SEX",
    "7": "SAB",
}
