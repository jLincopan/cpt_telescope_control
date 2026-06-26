import argparse
from spid_controller import SpidController
from time import sleep
import numpy as np
import matplotlib.pyplot as plt


def main():
    angulos_azimuth = np.linspace(0,359, 360)
    medidas_azimuth = np.zeros(360)
    angulos_elevacion = np.linspace(0,180, 181)
    medidas_elevacion = np.zeros(181) 
    az_inicial = 350
    el_inicial = 10

    '''
        10 9 8 7 6 5 4 3 2 1    0 11 12 13... 360
        az_inicial - a          a
        350 351 352 353...359   349 348... 0
        az_inicial + a          360 - a
    '''
    #Midiendo el patrón de radiación en azimuth
    for a in range(len(angulos_azimuth)):
        az = 0
        if az_inicial < 180:
            if az_inicial - a >= 0:
                az = int(angulos_azimuth[az_inicial-a])
            else:
                az = int(angulos_azimuth[a])
        elif az_inicial >= 180:
            az = 0
            if az_inicial + a <= 359:
                az = int(angulos_azimuth[az_inicial+a])
            else:
                az = int(angulos_azimuth[359-a])
        else:
            print("wtf?")
        medidas_azimuth[az] = az
        #Nos detenemos para que la antena deje de moverse tras cada movimiento
        #sleep(5)

    #Midiendo el patrón de radiación en elevación
    for a in range(len(angulos_elevacion)):
        el = 0
        if el_inicial < 90:
            if el_inicial - a >= 0:
                el = int(angulos_elevacion[el_inicial-a])
            else:
                el = int(angulos_elevacion[a])
        elif az_inicial >= 90:
            if el_inicial + a <= 180:
                el = int(angulos_elevacion[el_inicial+a])
            else:
                el = int(angulos_elevacion[180-a])
        else:
            print("wtf?")
        medidas_elevacion[el] = el
        #Nos detenemos para que la antena deje de moverse tras cada movimiento
        #sleep(5)
    #for a in range(0, 359):
    #    print(medidas_azimuth[a])
    print(medidas_azimuth)
    print(medidas_elevacion)
    raw_dB = 20 * np.log10(medidas_azimuth)
    datos_normalizados = raw_dB - np.max(raw_dB)
    theta = np.linspace(0, 2 * np.pi, 360)
    fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
    ax.set_theta_zero_location('N') 
    ax.set_theta_direction(-1)      
    ax.set_rticks([0, -3, -10, -20, -30])
    ax.plot(theta, datos_normalizados, color='blue', linewidth=1)

    ax.set_title("Patrón de radiación en azimuth (400 MHz, normalizado)", va='bottom')
    plt.savefig("patron_azimuth.png", dpi=300, bbox_inches="tight")
    np.savetxt("azimuth.csv", medidas_azimuth, fmt="%d")
    np.savetxt("elevation.csv", medidas_elevacion, fmt="%d")

    fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
    ax.set_theta_direction(1)
    ax.set_rticks([0, -3, -10, -20, -30])
    plt.tick_params(axis='x', labelsize=10)
    plt.tick_params(axis='y', labelsize=5)
    raw_dB = 20 * np.log10(medidas_elevacion)
    datos_normalizados = raw_dB - np.max(raw_dB)
    theta = np.linspace(0, np.pi, 181)
    ax.plot(theta, datos_normalizados, color='blue', linewidth=1)
    ax.set_title("Patrón de radiación en elevación (400 MHz, normalizado)", va='bottom')
    ax.set_thetamin(0)
    ax.set_thetamax(180)
    plt.savefig("patron_elevacion.png", dpi=300, bbox_inches="tight")
if __name__ == "__main__":
    main()