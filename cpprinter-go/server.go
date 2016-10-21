package main

import (
    "fmt"
    "os"
    "net"
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
    buff := make([]byte, 1024)

    reqLen, err := conn.Read(buff)
    if err != nil {
        fmt.Println("Error reading: ", err.Error())
    }
    fmt.Println(string(buff[:reqLen]))
    conn.Close()
}
