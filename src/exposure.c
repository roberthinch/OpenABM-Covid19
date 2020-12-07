#include "utilities.h"
#include "constant.h"
#include "params.h"
#include "individual.h"
#include "exposure.h"

/*****************************************************************************************
*  Name:		exposure_generate
*  Description: Generates the duration and the distance of an exposure
*  				Updates the paired interaction object which should record
*  				the same data (unlike whether it is traceable which can be one sided)
******************************************************************************************/
void exposure_generate( interaction *inter, exposure_parameters *params )
{
	inter->duration = exposure_duration_sample( params );
	inter->distance = exposure_distance_sample( params );
	inter->paired_interaction->distance = inter->distance;
	inter->paired_interaction->duration = inter->duration;
}

/*****************************************************************************************
*  Name:		exposure_distance_sample
*  Description: Samples the distance of an exposure
******************************************************************************************/
float exposure_distance_sample( exposure_parameters *params )
{
	double a, b;
	b = params->distance_sd * params->distance_sd / params->distance_mean;
	a = params->distance_mean / b;
	return( gsl_ran_gamma( rng, a, b ) );
}

/*****************************************************************************************
*  Name:		exposure_duration_sample
*  Description: Samples the duration of an exposure
******************************************************************************************/
float exposure_duration_sample( exposure_parameters *params )
{
	double a;
	a = params->duration_mean / ( params->duration_mean - params->duration_min );
	return( gsl_ran_pareto( rng, a, params->duration_min ) );
}

/*****************************************************************************************
*  Name:		exposure_transmission_factor
*  Description: Calculates the relative rate of transmission based upon the distance
*  				and duration of the interaction
******************************************************************************************/
float exposure_transmission_factor( exposure_parameters *params, float distance, float duration )
{
	return( duration / params->duration_mean );
}

/*****************************************************************************************
*  Name:		exposure_risk_score
*  Description: Calculates the risk score of a single interaction
******************************************************************************************/
float exposure_risk_score( exposure_parameters *params, int contact_time, float distance, float duration )
{
	return( duration / params->duration_mean );
}
