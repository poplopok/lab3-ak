ask_str: dd   "What is your name?\n", 0
hello_str: dd "Hello "
buf:    times  10 dd 0
buf_length: dd 10


_start:   add r2, r0, ask_str
loop_1:   lw  r1, r2
          beq r1, r0, ask
          out r1, 0
          add r2, r2, 1
          jmp loop_1

ask:     add  r2, r0, buf_length
         lw   r2, r2
         sub  r2, r2, 1
         add  r3, r0, buf
loop_2:  in      r1, 1
         beq     r1, r0, greet
         beq     r2, r0, greet
         sw      r3, r1
         add     r3, r3, 1
         jmp     loop_2

greet:    sw  r3, r0
          add r2, r0, hello_str
loop_3:   lw  r1, r2
          beq r1, r0, end
          out r1, 0
          add r2, r2, 1
          jmp loop_3

end:      hlt