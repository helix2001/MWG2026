import math
from math import nan, isnan

import matplotlib.pyplot as plt

from module.geo import *
from datetime import datetime
import module

ROLLING_WINDOW = 5

ID = "ID"
CALLSIGN = "INDICATIVO"
DEPARTURE = "ORIGEM"
DESTINATION = "DESTINO"
FIX = "FIXO"
TIMESTAMP = "HORA"

LATITUDE = 0
LONGITUDE = 1
# indice no tuplo do ATO - "Actual time over", hora de passagem sobre uma posição determinada
ATO = 2
# indice no tuplo do desvio lateral a calcular
LAT_DEV = 3


class Voo:

    def __init__(self, info: dict):
        self._id: int = info[ID]
        self._callsign: str = info[CALLSIGN]
        self._departure: str = info[DEPARTURE]
        self._destination: str = info[DESTINATION]
        self._profile: list = []
        self._reports: list = []
        self.desvios: list = []
        self.rolling_avg: list = []
        self._SLOP: int = -1

    def __str__(self):
        return "{}-{}, de {} para {}".format(self._id, self._callsign, self._departure, self._destination)

    def profile(self) -> list:
        return self._profile

    def reports(self) -> list:
        return self._reports

    def id(self) -> int:
        return self._id

    def callsign(self) -> str:
        return self._callsign

    def slop(self) -> int:
        return self._SLOP

    @staticmethod
    #   appends a fix with ATO to a list
    #   parameters
    #   fix:    string representing the fix
    #   ts:     string representing the timestamp
    #   returns
    #   list containing the added [lat:float, long:float, timestamp:datetime]
    def append_fix_ato(fix: str, ts: str, fix_list: list) -> tuple[float, float, datetime, float]:
        # determina os valores de latitude e longitude
        lat, lon = str_to_latlong(fix)
        # determina a hora de passagem
        time_stamp = datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
        # se não há erros, adiciona a hora ao final da lista de fixos
        if lat != ERROR_LATLONG and lon != ERROR_LATLONG:
            # adiciona o resultado à lista, reservando espaço para o calculo do desvio
            # ao definir o desvio não calculado como nan, mais tarde será fácil perceber
            # se conseguimos cálcula-lo, ou não.
            fix_list.append([lat, lon, time_stamp, nan])
        # retorna o valor introduzido, reservando espaço para o cálculo do desvio
        return lat, lon, time_stamp, nan

    # uses append_fix_ato to append a fix to the flight's profile
    def append_profile(self, fix: str, ts: str) -> tuple[float, float, datetime, float]:
        return self.append_fix_ato(fix, ts, self._profile)

    # uses append_fix_ato to append a fix to the flight's reports list
    def append_report(self, fix: str, ts: str) -> tuple[float, float, datetime, float]:
        return self.append_fix_ato(fix, ts, self._reports)

    # calcular os desvios para cada um dos pontos reportados
    def calc_lat_dev(self):
        # garantir que as listas com o perfil e reportes do voo estão ordenadas
        # por ordem crescente de hora de passagem
        self._profile.sort(key=lambda x: x[2])
        self._reports.sort(key=lambda x: x[2])

        # ponto reportado a calcular o desvio
        reported: int = 0

        # ponto inicial do segmento de rota a considerar para o cálculo do desvio
        fix: int = 0

        # o ciclo é executado enquanto o ponto reportado não for o ultimo da lista
        # e enquanto o ponto inicial do segmento a analisar não for o ultimo da rota
        while reported < len(self._reports) and fix < len(self._profile)-1:
            # se a hora do ponto reportado for anterior à hora do segmento de rota
            if self._reports[reported][ATO] < self._profile[fix][ATO]:
                # passa para o ponto reportado seguinte
                reported += 1

            # se a hora do ponto reportado for posterior ou igual  à hora de passagem
            # no 1º fixo do segmento, mas anterior à hora de passagem no 2º ponto do segmento,
            # efetua o calculo do desvio lateral.
            elif self._profile[fix][ATO] <= self._reports[reported][ATO]:
                if self._profile[fix+1][ATO] > self._reports[reported][ATO]:
                    # ponto reportado pelo voo
                    lat, long, to, dummy = self._reports[reported]
                    # inicio do troço de rota
                    lat1, long1, to1, dummy = self._profile[fix]
                    # final do troço de rota
                    lat2, long2, to2, dummy = self._profile[fix+1]

                    # calcula o desvio lateral do ponto reportado em relação ao
                    # troço de rota fix1 -> fix2
                    dev_lat: float = module.geo.x_track_error(lat1, long1, lat2, long2, lat, long)/1852
                    # acrescenta o valor do desvio ao tuplo que contem os dados do reporte
                    # se este estiver dentro dos intervalos aceitáveis
                    if -0.1 <= dev_lat < 2.5:
                        self._reports[reported][LAT_DEV] = dev_lat
                    # passa para o reporte seguinte
                    reported += 1
                # se a hora do ponto reportado for posterior ou igual à hora do 2º fixo do
                # segmento de rota a considerar, passa para o segmento seguinte.
                elif self._reports[reported][ATO] >= self._profile[fix+1][ATO]:
                    fix += 1

        # define uma lista com os valores dos desvios, removendo os que não foram calculados.
        # esta lista está ordenada por ordem de reporte de posição, ou seja, o 1º desvio corresponde
        # ao primeiro reporte dentro da rota conhecida, e por ai fora
        self.desvios = list(filter(lambda x: not math.isnan(x), map(lambda r: r[3], self._reports)))

        if len(self.desvios) != 0:
            # calcular a "rolling average dos desvios"
            diff = ROLLING_WINDOW//2
            for d in range(len(self.desvios)):
                # garantir que começãmos no inicio da array
                start = max(0, d-diff)
                end = d + diff + 1
                values = self.desvios[start:end]
                self.rolling_avg.append(sum(values) / len(values))

            # calcular o SLOP como a média das "rolling averages"
            temp = sum(self.rolling_avg)/len(self.rolling_avg)
            self._SLOP = module.geo.slop(temp)

            # print(self.desvios)
            # print(self.rolling_avg)

    def plot_route(self):
        """
        Utiliza matplotlib para desenhar o mapa dos reportes de posição, considerando uma projeção plana.
        Não será muito correto, mas dará para ter uma ideia da posição dos reportes em relação às ilhas.
        :return: Nil
        :rtype: Nil
        """

        # criar lista com as latitudes e longitudes dos reportes e dos ponto do perfil do voo
        lat_reportes = list(map(lambda x: x[0], self._reports))
        long_reportes = list(map(lambda x: x[1], self._reports))

        lat_perfil = list(map(lambda x: x[0], self._profile))
        long_perfil = list(map(lambda x: x[1], self._profile))

        # definir dimensões do mapa
        # abcissas , longitudes, W é negativo
        # representa pontos entre 10N e 50N
        # ordenadas , latitudes, E é negativo
        # representa pontos entre 50W e 05W
        plt.figure(figsize=(9, 5))
        plt.title(label=str(self))
        plt.ylim(10, 50)
        plt.xlim(-50, -5)

        # desenhar série do perfil do voo, linha verde
        plt.scatter(long_perfil, lat_perfil)
        plt.plot(long_perfil, lat_perfil, linewidth=1.0, color="green", markersize=0.5)

        # desenhar série com os reportes, pontos isolados, pontos azuis
        plt.scatter(long_reportes, lat_reportes)
        plt.plot(long_reportes, lat_reportes, linewidth=0.0, color="blue")

        # desenhar Santa Maria e Flores, como referência
        plt.scatter([-25, -31], [37, 41])
        plt.plot([-25, -31], [37, 41], linewidth=0.0, color="red")

        plt.show()

    def plot_dev(self):
        """
        Utiliza matplotlib para desenhar uma linha com os valores dos desvios e outra com
        os valores da média "volante"
        :return: Nil
        :rtype: Nil
        """

        # criar lista com os indexes dos desvios
        index_devs = list(map(lambda x: self.desvios.index(x), self.desvios))

        # definir dimensões do mapa
        # abcissas , contém o index
        # ordenadas , valor do desvio
        plt.figure(figsize=(9, 5))

        plt.title(label=str(self)+", SLOP "+str(self.slop()))
        plt.ylim(-0.1, 2.6)
        plt.xlim(0, len(index_devs))

        # desenhar série dos desvios calculados, linha verde
        plt.plot(index_devs, self.desvios, linewidth=1.0, color="green")
        # desenhar série das "rolling averages"
        plt.plot(index_devs, self.rolling_avg, linewidth=1.0, color="red")

        plt.show()


