_start: in      r1, 1
        beq     r1, r0, end
        out     r1, 0
        jmp     _start
end:    hlt