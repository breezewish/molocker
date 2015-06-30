#include "HardwareEventListener.h"
#include <strsafe.h>

#define BUFSIZE 512

#include <string>
#include <stdarg.h>
#include <stdio.h>

void debug(const char * sz, ...)
{
	char szData[512] = { 0 };

	va_list args;
	va_start(args, sz);
	_vsnprintf_s(szData, sizeof(szData)-1, sz, args);
	va_end(args);

	OutputDebugStringA(szData);
}

BOOL readPipeBytes(HANDLE hFile, LPVOID buffer, DWORD byteToRead)
{
	DWORD out, readed = 0;
	for (;;)
	{
		BOOL success = ReadFile(hFile, (VOID*)((UINT)buffer + readed), byteToRead, &out, NULL);
		if (success == 0 || out == 0) {
			if (GetLastError() != ERROR_MORE_DATA) {
				return 0;
			}
		}
		readed += out;
		if (readed >= byteToRead) {
			break;
		}
	}

	return 1;
}

CHardwareEventListener::CHardwareEventListener() : _hPipeBroadcast(NULL), _hInst(NULL), _fConnected(FALSE), _fSupposeLogin(FALSE), _pProvider(NULL)
{
}

CHardwareEventListener::~CHardwareEventListener()
{
	if (_hPipeBroadcast != NULL) {
		DisconnectNamedPipe(_hPipeBroadcast);
		CloseHandle(_hPipeBroadcast);
	}

    if (_pProvider != NULL)
    {
        _pProvider->Release();
        _pProvider = NULL;
    }
}

// Performs the work required to spin off our message so we can listen for events.
HRESULT CHardwareEventListener::Initialize(__in CSampleProvider *pProvider)
{
    HRESULT hr = S_OK;

    if (_pProvider != NULL)
    {
        _pProvider->Release();
    }
    _pProvider = pProvider;
    _pProvider->AddRef();
    
    CreateThread(NULL, 0, _ThreadEventProc, this, 0, NULL);
	
    return hr;
}

// Wraps our internal connected status so callers can easily access it.
BOOL CHardwareEventListener::GetConnectedStatus()
{
    return _fConnected;
}

BOOL CHardwareEventListener::GetSupposeLoginStatus()
{
	return _fSupposeLogin;
}

DWORD WINAPI CHardwareEventListener::_ThreadEventProc(__in LPVOID lpParameter)
{
    CHardwareEventListener *pHardwareEventListener = static_cast<CHardwareEventListener *>(lpParameter);
    if (pHardwareEventListener == NULL)
    {
        return 0;
    }

	LPTSTR lpszPipename = TEXT("\\\\.\\pipe\\molocker_event");

	HANDLE hPipe = CreateNamedPipe(
		lpszPipename,             // pipe name 
		PIPE_ACCESS_DUPLEX,       // read/write access 
		PIPE_TYPE_MESSAGE |       // message type pipe 
		PIPE_READMODE_MESSAGE |   // message-read mode 
		PIPE_WAIT,                // blocking mode 
		PIPE_UNLIMITED_INSTANCES, // max. instances  
		BUFSIZE,                  // output buffer size 
		BUFSIZE,                  // input buffer size 
		0,                        // client time-out 
		NULL);                    // default security attribute 

	if (hPipe == INVALID_HANDLE_VALUE)
	{
		debug("CreateNamedPipe failed, ERROR=%d", GetLastError());
		return 0;
	}

	HANDLE hPython;

	SHELLEXECUTEINFO shellExInfo;

	shellExInfo.cbSize = sizeof(SHELLEXECUTEINFO);
	shellExInfo.fMask = SEE_MASK_NOCLOSEPROCESS;
	shellExInfo.hwnd = NULL;
	shellExInfo.lpVerb = L"open";
	shellExInfo.lpFile = L"C:\\Anaconda\\python.exe";
	shellExInfo.lpParameters = L"C:\\molocker\\src\\Authorize.py";
	shellExInfo.lpDirectory = L"C:\\molocker\\src";
	shellExInfo.nShow = SW_SHOW;
	shellExInfo.hInstApp = NULL;

	ShellExecuteEx(&shellExInfo);
	hPython = shellExInfo.hProcess;

	ConnectNamedPipe(hPipe, NULL);
	char buffer[BUFSIZE];

	for (;;)
	{
		INT32 msgSize = 0;
		if (readPipeBytes(hPipe, &msgSize, 4) == 0) break;
		if (readPipeBytes(hPipe, buffer, msgSize) == 0) break;
		buffer[msgSize] = '\0';

		if (buffer[0] == '1')
		{
			// connected
			pHardwareEventListener->_fConnected = true;
			pHardwareEventListener->_pProvider->OnConnectStatusChanged();
		}
		else if (buffer[0] == '2')
		{
			// disconnected
			pHardwareEventListener->_fConnected = false;
			pHardwareEventListener->_pProvider->OnConnectStatusChanged();
		}
		else if (buffer[0] == '3')
		{
			// password not correct
		}
		else if (buffer[0] == '4')
		{
			char* dlUser = strstr(buffer, ":");
			char* dlPass = strstr(dlUser + 1, ":");
			*dlUser = '\0';
			*dlPass = '\0';
			dlUser++;
			dlPass++;
			pHardwareEventListener->_fSupposeLogin = true;
			pHardwareEventListener->_pProvider->Login(dlUser, dlPass);
			pHardwareEventListener->_pProvider->OnConnectStatusChanged();
			TerminateProcess(hPython, 1);
		}
	}

	debug("[ERROR] Pipe Event disconnected from auth service");

	DisconnectNamedPipe(hPipe);
	CloseHandle(hPipe);

    return 0;
}