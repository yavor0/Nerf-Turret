use std::sync::Arc;

use iced::widget::image::Image;
use iced::Event;
use iced::{
    alignment::Horizontal,
    alignment::Vertical,
    widget::{text_input, Button, Column, Container, Row, Text},
    Alignment, Application, Command, Element, Length, Settings, Theme
};
use iced::{executor, mouse};
use iced_aw::{Card, Modal};
use iced_native::image::Handle;
use iced::theme;
mod com_ard;
use com_ard::ComArd;
use opencv::{
    prelude::*,
    videoio::{self, VideoCapture},
    imgproc::{COLOR_RGB2RGBA, cvt_color}
};



fn main() -> iced::Result {
    TurretControls::run(Settings::default())
}

#[derive(Clone, Debug)]
enum Message {
    OpenModal,
    CloseModal,
    OkButtonPressed,
    OnInputChanged(String),
    MouseEvent(Event),
    MotorButtonPressed,
    SwitchModeButtonPressed
}

struct TurretControls {
    show_modal: bool,
    port: String,
    connect_button_image: String,
    bluetooth_button_image: String,
    motor_on_image: String,
    motor_btn_image: String,
    motor_btn_pressed: bool,
    swtch_mode_btn_pressed: bool,
    pad: String,
    x: i32,
    y: i32,
    ard: ComArd,
    cap: VideoCapture,
    image_handle: Handle,

}

impl Default for TurretControls {
    fn default() -> TurretControls {
        let mut cap = VideoCapture::new(1, videoio::CAP_ANY).unwrap();
        let opened = cap.is_opened().unwrap();
        if !opened {
            panic!("Unable to open default camera!");
        }
        cap.set(videoio::CAP_PROP_FRAME_WIDTH, 640.0).unwrap();
        cap.set(videoio::CAP_PROP_FRAME_HEIGHT, 480.0).unwrap();

        let mut mat = Mat::default();
        cap.read(&mut mat).unwrap();
        let mut gray = Mat::default();
        cvt_color(&mat, &mut gray, COLOR_RGB2RGBA, 0).unwrap();
        let gray_data = gray.data();
        println!("{} {} {} {} ", gray.cols(), gray.rows(), gray.channels(), gray.total());
        let gray_slice = unsafe { std::slice::from_raw_parts(gray_data, (gray.total() * gray.channels() as usize) as usize) };
        // let image_handle = Handle::from_pixels(gray.cols() as u32, gray.rows() as u32, gray_slice);

        let image_handle = Handle::from_memory(gray_slice.to_vec());
        println!("Image handle: {:?}", image_handle);

        TurretControls {
            show_modal: false,
            port: String::from("COM9"),
            connect_button_image: String::from("./GUI/connect_button.png"),
            bluetooth_button_image: String::from("./GUI/not_connect.png"),
            motor_on_image: String::from("./GUI/motor_on.png"),
            motor_btn_image: String::from("./GUI/motor_off_blocked.png"),
            motor_btn_pressed: false,
            swtch_mode_btn_pressed: false,
            pad: String::from("./GUI/pad-pc_blocked.png"),
            x: 0,
            y: 0,
            ard: ComArd::new(),
            cap: cap,
            image_handle: image_handle,
        }
    }
}

impl Application for TurretControls {
    type Message = Message;
    type Theme = Theme;
    type Executor = executor::Default;
    type Flags = ();

    fn new(_flags: ()) -> (TurretControls, Command<Message>) {
        (TurretControls::default(), Command::none())
    }

    fn title(&self) -> String {
        String::from("Nerf turret controller")
    }

    fn theme(&self) -> Theme {
        Self::Theme::Dark
    }

    fn update(&mut self, message: Self::Message) -> Command<Message> {
        let opened = self.cap.is_opened().unwrap();
        if opened  && self.show_modal == true{
            let mut mat = Mat::default();
            self.cap.read(&mut mat).unwrap();
            let mut gray = Mat::default();
            cvt_color(&mat, &mut gray, COLOR_RGB2RGBA, 0).unwrap();
            let gray_data = mat.data();
            let gray_slice = unsafe { std::slice::from_raw_parts(gray_data, (gray.total() * gray.channels() as usize) as usize) };
            
            self.image_handle = Handle::from_pixels(gray.cols() as u32, gray.rows()  as u32, gray_slice);
            // println!("Image handle: {:?}", self.image_handle);
        }

        match message {
            Message::OpenModal => self.show_modal = true,
            Message::CloseModal => self.show_modal = false,
            Message::OkButtonPressed => {
                self.show_modal = false;
                //ard connect
                println!("Port number: {}", self.port);
            }
            Message::MouseEvent(event) => match event {
                Event::Mouse(mouse_event) => match mouse_event {
                    mouse::Event::CursorMoved { position } => {
                        println!("Mouse cursor moved : {}, {}", position.x, position.y);
                    }
                    _ => {}
                },
                _ => {}
            },
            Message::OnInputChanged(port) => self.port = port,
            Message::MotorButtonPressed => {
                if self.motor_btn_pressed {
                    self.motor_btn_pressed = false;
                    self.motor_btn_image = String::from("./GUI/motor_on.png");
                } else {
                    self.motor_btn_pressed = true;
                    self.motor_btn_image = String::from("./GUI/motor_off.png");
                }
            }
            Message::SwitchModeButtonPressed => {
                if self.swtch_mode_btn_pressed {
                    self.swtch_mode_btn_pressed = false;
                    self.motor_on_image = String::from("./GUI/motor_on.png");
                } else {
                    self.swtch_mode_btn_pressed = true;
                    self.motor_on_image = String::from("./GUI/motor_off.png");
                }
            }
        }
        // self.last_message = Some(message);

        return Command::none();
    }

    fn subscription(&self) -> iced::Subscription<Self::Message> {
        iced::subscription::events().map(Message::MouseEvent)
    }

    fn view(&self) -> Element<'_, Self::Message> {
        let content = Container::new(
            Row::new()
                .spacing(10)
                .align_items(Alignment::Center)
                .push(
                    Column::new()
                        .spacing(10)
                        .align_items(Alignment::Center)
                        .push(
                            Button::new(
                                Image::new(self.bluetooth_button_image.as_str())
                                    .width(64)
                                    .height(64),
                            )
                            .on_press(Message::OpenModal)
                            .style(theme::Button::Text),
                        )
                        .push(
                            Button::new(
                                Image::new(self.motor_btn_image.as_str())
                                    .width(64)
                                    .height(64),
                            )
                            .on_press(Message::MotorButtonPressed)
                            .style(theme::Button::Text),
                        )
                        .push(
                            Button::new(
                                Image::new(self.motor_btn_image.as_str())
                                    .width(64)
                                    .height(64),
                            )
                            .on_press(Message::MotorButtonPressed)
                            .style(theme::Button::Text),
                        ),
                )
                .push(Image::new(self.image_handle.clone()).width(Length::Fill).height(Length::Fill)),
        )
        .align_x(Horizontal::Center)
        .align_y(Vertical::Center)
        .width(Length::Fill)
        .height(Length::Fill)
        .center_x()
        .center_y();
        Modal::new(self.show_modal, content, || {
            Card::new(
                Text::new("Port selection"),
                Column::new()
                    .spacing(10)
                    .padding(5)
                    .width(Length::Fill)
                    .push(
                        text_input::TextInput::new("Enter port number", &self.port)
                            .on_input(|port| Message::OnInputChanged(port)),
                    ),
            )
            .foot(
                Row::new()
                    .spacing(10)
                    .align_items(Alignment::Center)
                    .padding(5)
                    .width(Length::Fill)
                    .push(
                        Button::new(
                            Image::new(self.connect_button_image.as_str())
                                .width(128)
                                .height(64),
                        )
                        .on_press(Message::OkButtonPressed)
                        .style(theme::Button::Text),
                    ),
            )
            .max_width(300.0)
            //.width(Length::Shrink)
            .on_close(Message::CloseModal)
            .into()
        })
        .backdrop(Message::CloseModal)
        .on_esc(Message::CloseModal)
        .into()
    }
}