package main

import (
    "fmt"
    "os"
    "net"
    //"github.com/tarm/serial"
    "github.com/mikepb/go-serial"
)

func main() {
    listener, err := net.Listen("tcp", "0.0.0.0:5555")
    if err != nil {
        fmt.Println("Error listening: ", err.Error())
        os.Exit(1)
    }
    defer listener.Close()

    fmt.Println("Listening on 0.0.0.0:5555")
    for {
        conn, err := listener.Accept()
        if err != nil {
            fmt.Println("Error accepting: ", err.Error())
            os.Exit(1)
        }

        go handleConnection(conn)
    }
}

func handleConnection(conn net.Conn) {
    buff := make([]byte, 8192)

    reqLen, err := conn.Read(buff)
    if err != nil {
        fmt.Println("Error reading: ", err.Error())
    }
    WriteToSerial(string(buff[:reqLen]))
    fmt.Println(string(buff[:reqLen]))
    conn.Close()
}

func WriteToSerial(message string) {
    options := serial.RawOptions
    options.BitRate = 9600
    options.Mode = 1
    p, err := options.Open("/dev/ttyUSB0")
    if err != nil {
        println(err.Error())
        return
    }
    defer p.Close()

    bytes, err := p.WriteString(message)
    if err != nil {
        println(err.Error())
        return
    }
    fmt.Printf("%d bytes written\n", bytes)
}

//func WriteToSerial(message string) {
    //serialConfig := &serial.Config{Name: "ttyUSB0", Baud: 9600}

    //ser, err := serial.OpenPort(serialConfig)
    //if err != nil {
        //println(err.Error())
        //return
    //}
    //defer ser.Close()
    //bytes, err := ser.Write([]byte(message))
    //if err != nil {
        //println("Error writing to serial connection. ", err.Error())
        //return
    //}
    //println(string(bytes) + "bytes written")
//}
