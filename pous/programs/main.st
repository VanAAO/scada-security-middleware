PROGRAM main
VAR
	Temperature : int := 22;
	Humidity : int := 45;
	SetpointTemp : int := 22;
	SetpointHumid : int := 50;
	ChillerStatus : bool := FALSE;
	HumidifierStatus : bool := FALSE;
END_VAR

(* HVAC Control Logic for Data Center *)

(* Simple temperature control *)
IF Temperature > SetpointTemp THEN
    ChillerStatus := TRUE;  (* Turn ON chiller if too hot *)
ELSE
    ChillerStatus := FALSE; (* Turn OFF chiller if cool enough *)
END_IF;

(* Simple humidity control *)
IF Humidity < SetpointHumid THEN
    HumidifierStatus := TRUE;  (* Turn ON humidifier if too dry *)
ELSE
    HumidifierStatus := FALSE; (* Turn OFF humidifier if humid enough *)
END_IF;

Temperature VAR INT %MW0 22
Humidity VAR INT %MW1 45
SetpointTemp VAR INT %MW2 22
SetpointHumid VAR INT %MW3 50
ChillerStatus VAR BOOL %QX0.0 FALSE
HumidifierStatus VAR BOOL %QX0.1 FALSE

END_PROGRAM