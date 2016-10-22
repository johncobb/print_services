extern crate serial;

use std::net::{TcpListener, TcpStream};
use std::io::Read;
use std::io;

use serial::prelude::*;
use std::io::prelude::Write;

fn main() {
    let listener = TcpListener::bind("0.0.0.0:5555").unwrap();

    //listener.incoming is an iterator over the accepts
    for stream in listener.incoming() {
        match stream {
            Ok(mut stream) => {
                handle_connection(&mut stream);
            }
            Err(_) => {println!("Connection error"); }
        }
    }
    println!("Hello, world!");
}

fn handle_connection(stream: &mut TcpStream) {
    let mut label: Vec<u8> = Vec::new();
    let _ = stream.read_to_end(&mut label).unwrap();
    print_label(String::from_utf8(label).unwrap());
}

fn print_label(label: String) -> io::Result<()> {
    let mut port = serial::open("/dev/ttyUSB0").unwrap();
    try!(port.reconfigure(&|settings| {
        try!(settings.set_baud_rate(serial::Baud9600));
        settings.set_char_size(serial::Bits8);
        settings.set_parity(serial::ParityNone);
        settings.set_stop_bits(serial::Stop1);
        settings.set_flow_control(serial::FlowNone);
        Ok(())
    }));

    try!(port.write(label.as_bytes()));

    println!("{}", label);
    return Ok(());
}
