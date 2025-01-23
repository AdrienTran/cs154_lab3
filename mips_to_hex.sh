# cs154 lab6

# $1 : MIPS source filename
# $2 : output filename

mkdir -p dump
cd dump

spim -dump -delayed_branches -notrap -file ../$1

cut -c16-23 text.asm > hex.txt
sed -i '1,2d' hex.txt

cd ..
mv dump/hex.txt $2
