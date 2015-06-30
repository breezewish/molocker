#pragma once

#include <windows.h>
#include "CSampleProvider.h"

class CSampleProvider;

class CHardwareEventListener
{
public:
    CHardwareEventListener();
    ~CHardwareEventListener();
    HRESULT Initialize(__in CSampleProvider *pProvider);
    BOOL GetConnectedStatus();
	BOOL GetSupposeLoginStatus();

private:
    static DWORD WINAPI _ThreadEventProc(__in LPVOID lpParameter);
	static DWORD WINAPI _ThreadBroadcastProc(__in LPVOID lpParameter);
    CSampleProvider*            _pProvider;        // Pointer to our owner.
    HINSTANCE                   _hInst;            // Current instance
    BOOL                        _fConnected;       // Whether or not we're connected.
	BOOL                        _fSupposeLogin;    // Whether we are going to auto login.
	HANDLE                      _hPipeBroadcast;   // Broadcast pipe
};
