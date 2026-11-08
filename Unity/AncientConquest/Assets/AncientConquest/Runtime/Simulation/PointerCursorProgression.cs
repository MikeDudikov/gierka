using System;
namespace AncientConquest.Simulation
{
    /// <summary>Source0/5/6/7 cursor and normal-map TAKE_CMD cached-millisecond branch.</summary>
    public sealed class PointerCursorProgression
    {
        public readonly struct Snapshot
        {
            public int CursorType { get; }
            public bool GreenVariant { get; }
            public int CursorFrame { get; }
            public int ScreenX { get; }
            public int ScreenY { get; }
            public bool CursorVisible { get; }
            public int CursorWorldX { get; }
            public int CursorWorldY { get; }
            public uint CursorLastTick { get; }
            public uint CursorInterval { get; }
            public bool ConfirmExists { get; }
            public int ConfirmFrame { get; }
            public int ConfirmDrawnFrame { get; }
            public bool ConfirmVisible { get; }
            public int ConfirmWorldX { get; }
            public int ConfirmWorldY { get; }
            public uint ConfirmLastTick { get; }
            internal Snapshot(PointerCursorProgression p)
            {
                CursorType=p.type;GreenVariant=p.green;CursorFrame=p.frame;ScreenX=p.x;ScreenY=p.y;
                CursorVisible=p.visible;CursorWorldX=unchecked(p.x+(p.type==7?-18:0));
                CursorWorldY=unchecked(p.y+(p.type==7?-17:0));CursorLastTick=p.stamp;CursorInterval=p.interval;
                ConfirmExists=p.confirm;ConfirmFrame=p.confirmFrame;ConfirmDrawnFrame=p.confirmDrawn;
                ConfirmVisible=p.confirmVisible;ConfirmWorldX=p.confirmX;ConfirmWorldY=p.confirmY;ConfirmLastTick=p.confirmStamp;
            }
        }
        private int type=-1,frame,x,y,confirmFrame,confirmDrawn=-1,confirmX,confirmY;
        private bool green,visible,confirm,confirmVisible;
        private uint stamp,interval=500,confirmStamp;
        public Snapshot Current=>new Snapshot(this);
        public bool LastStepCursorPublishesPose { get; private set; }
        public bool LastStepConfirmPublishesPose { get; private set; }
        public bool LastStepDeletesConfirm { get; private set; }
        public bool SetCursor(int cursorType,bool greenVariant,uint cachedMilliseconds,int screenX,int screenY)
        {
            if(cursorType!=0 && cursorType!=5 && cursorType!=6 && cursorType!=7)
                throw new NotSupportedException("Only normal source cursor types0,5,6,7 are supported.");
            ResetEffects();
            if(type==cursorType && green==greenVariant)return false;
            type=cursorType;green=greenVariant;
            // SetImagesReg preserves an already drawn node's valid frame.
            // Only SEA has multiple frames among these normal cursor types.
            if(type!=7)frame=0;
            DrawCore(cachedMilliseconds,screenX,screenY);
            interval=type==7?150u:10000u;
            return true;
        }
        public void Draw(uint cachedMilliseconds,int screenX=-1,int screenY=-1)
        {
            ResetEffects();DrawCore(cachedMilliseconds,screenX,screenY);
        }
        public void Confirm(int worldX,int worldY)
        {
            ResetEffects();LastStepDeletesConfirm=confirm;confirm=true;confirmVisible=false;
            confirmFrame=0;confirmDrawn=-1;confirmStamp=0;
            confirmX=unchecked(worldX-11);confirmY=unchecked(worldY-24);
        }
        private void DrawCore(uint now,int screenX,int screenY)
        {
            if(type<0)return;
            bool publish=false;
            if(screenX!=-1){x=screenX;publish=true;}
            if(screenY!=-1){y=screenY;publish=true;}
            if(unchecked(interval+stamp)<=now)
            {
                stamp=now;frame=(frame+1)%(type==7?4:1);publish=true;
            }
            if(publish){visible=true;LastStepCursorPublishesPose=true;}
            if(!confirm)return;
            if(confirmFrame<3)
            {
                if(unchecked(250u+confirmStamp)<=now)
                {
                    confirmStamp=now;confirmFrame++;confirmDrawn=confirmFrame;
                    confirmVisible=true;LastStepConfirmPublishesPose=true;
                }
            }
            else
            {
                confirm=false;confirmVisible=false;LastStepDeletesConfirm=true;
            }
        }
        private void ResetEffects()
        {
            LastStepCursorPublishesPose=false;LastStepConfirmPublishesPose=false;LastStepDeletesConfirm=false;
        }
    }
}
