package main

import (
    "os"
    "github.com/tarm/serial"
)

func main() {
    if len(os.Args) != 2 {
        println("Invalid arguments: ", os.Args)
        os.Exit(-1)
    }

    WriteToSerial(os.Args[1])
}

func WriteToSerial(message string) {
    serialConfig := &serial.Config{Name: "/dev/ttyUSB0", Baud: 9600}

    ser, err := serial.OpenPort(serialConfig)
    if err != nil {
        println(err.Error())
        return
    }
    defer ser.Close()
    _, err = ser.Write([]byte(message))
    if err != nil {
        println("Error writing to serial connection. ", err.Error())
        return
    }
}
