/*
 * exposure.h
 *
 *  Created on: 24 Nov 2020
 *      Author: hinchr
 */

#ifndef SRC_EXPOSURE_H_
#define SRC_EXPOSURE_H_

#include "params.h"
#include "individual.h"

void exposure_generate( interaction*, exposure_parameters* );
float exposure_duration_sample( exposure_parameters* );
float exposure_distance_sample( exposure_parameters* );
float exposure_transmission_factor( exposure_parameters*, float, float );

#endif /* SRC_EXPOSURE_H_ */
