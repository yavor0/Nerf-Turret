use serialport::{SerialPort, Error};

pub struct ComArd {
    port: Box<dyn SerialPort>,
}

impl ComArd {
    fn connect(port_name: &str, baud_rate: u32) -> Result<Self, Error> {
        let port = serialport::new(port_name, baud_rate)
        .open().expect("Failed to open port");

        Ok(ComArd { port : port})
    }

    fn send(&mut self, data: &[u8]) -> Result<(), Error> {
        self.port.write(data)?;
        Ok(())
    }
}
