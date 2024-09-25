hello:    dd "Hello, World!", 0

_start: add   r2, r0, hello
loop:   lw  r1, r2
     beq r1, r0, end
     out r1, 0
     add r2, r2, 1
     jmp loop
end: hlt
