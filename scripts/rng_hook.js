'use strict';

/*
 * rng_hook.js
 *
 * Frida script used during the data collection stage
 * overrides the Doom process at runtime and collects RNG values 
 * produced by the targeted functions (M_Random, P_Random)
 *
 * it does not modify the Doom source code or the gameplay behavior,
 * it only collects selected inputs and sends them to run_manager.py for logging
 *
 * USAGE: it runs automatically with run_manager.py, cannot be used alone
 */

// GLOBAL STATE
let started = false;
let startTime = 0;

// warmup phase tracker, used to discard initialization-related events
let warmupComplete = false;
let warmupDiscardCount = 1000;
let discarded = 0;

// gives each captured RNG value a sequential identifier
let rngCounter = 0;

// sends structured events to run_manager.py
function emit(obj) {
    send(obj);
}

// prints debugging messages to the terminal
function log(msg) {
    console.log(msg);
}

// Attaches a Frida hook to a function identified by its symbol name.
function attachHook(symbol, callbacks) {
    try {
        const addr = DebugSymbol.getFunctionByName(symbol);

        Interceptor.attach(addr, callbacks);

        emit({
            type: "hook_status",
            symbol: symbol,
            status: "attached"
        });

    } catch (e) {

        emit({
            type: "hook_status",
            symbol: symbol,
            status: "failed",
            error: String(e)
        });
    }
}

// uses level setup (P_SetupLevel) as the start point of the gameplay session
attachHook("P_SetupLevel", {
    
    onEnter(args) {

        if (!started) {

            started = true;
            startTime = Date.now();

            emit({
                type: "session_start",
                timestamp: startTime,
                warmup_discard_count: warmupDiscardCount
            });
        }
    }
});

// attaches a hook to an RNG function and captures its returned value
function attachRngHook(symbol) {

    attachHook(symbol, {

        onLeave(retval) {

            // ignore all RNG before gameplay starts
            if (!started)
                return;

            //discards early RNG calls caused by level setup and startup activity
            if (!warmupComplete) {

                discarded++;

                if (discarded >= warmupDiscardCount) {

                    warmupComplete = true;

                    emit({
                        type: "warmup_complete",
                        discarded_events: discarded,
                        timestamp: Date.now()
                    });
                }

                return;
            }

            // sends one valid RNG event to the logging pipeline
            emit({
                id: rngCounter++,

                type: "rng",

                function: symbol,

                value: retval.toInt32(),

                timestamp: Date.now(),

                uptime_ms: Date.now() - startTime
            });
        }
    });
}

// ,ain Doom RNG functions monitored
attachRngHook("P_Random");
attachRngHook("M_Random");

// attaches timing hooks to input-related functions
function attachInputHook(symbol) {

    attachHook(symbol, {

        onEnter(args) {

            if (!started || !warmupComplete)
                return;

            emit({
                type: "input",

                function: symbol,

                timestamp: Date.now(),

                uptime_ms: Date.now() - startTime
            });
        }
    });
}

// optional input hooks used for player-interaction correlation analysis
attachInputHook("G_Responder");
attachInputHook("I_GetEvent");

// reports that the instrumentation script was loaded and configured
emit({
    type: "instrumentation_ready",

    timestamp: Date.now(),

    configuration: {

        warmup_discard_count: warmupDiscardCount,

        hooks: [
            "P_SetupLevel",
            "P_Random",
            "M_Random",
            "G_Responder",
            "I_GetEvent"
        ]
    }
});

