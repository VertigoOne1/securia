# Infrastructure

Everything infrastructure

Start with k3s and then the rest

This entire directory needs to become an actions run with the only a few inputs to configure everything

## Scrap laptops -> servers

dozer - i5 8gb - .44
plucky - i3 8gb - .45
choef - i5 8Gb - .46
rabbit - i3 8gb - .47

basics

ubuntu minimal -> noble

Turn off lid stuff

https://www.baeldung.com/linux/disable-suspend-lid-close

basic netplan

network:
    ethernets:
        enp1s0:
            addresses:
            - 10.0.0.xxx/24
            dhcp4: false
            nameservers:
                addresses:
                - 10.0.0.2
                - 8.8.8.8
            routes:
            -   to: default
                via: 10.0.0.2
    version: 2

## Minimum

`apt install vim lm-sensors iputils-ping curl htop`

dozer is ready for k3s

Some future work, text to speech

https://huggingface.co/SWivid/F5-TTS

deeplab can be optimised with TPU's

https://pytorch.org/hub/pytorch_vision_deeplabv3_resnet101/

https://coral.ai/docs/edgetpu/benchmarks/