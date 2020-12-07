/*
 * exposure.h
 *
 *  Created on: 24 Nov 2020
 *      Author: hinchr
 */

#ifndef EXPOSURE_H_
#define EXPOSURE_H_

/************************************************************************/
/******************************* Includes *******************************/
/************************************************************************/

#include "params.h"
#include "individual.h"

/************************************************************************/
/******************************  Functions  *****************************/
/************************************************************************/

float exposure_duration_sample( exposure_parameters* );
float exposure_distance_sample( exposure_parameters* );
float exposure_transmission_factor( exposure_parameters*, float, float );
float exposure_risk_score( exposure_parameters *params, int, float, float );
void exposure_generate( interaction*, exposure_parameters* );

#endif /* EXPOSURE_H_ */
