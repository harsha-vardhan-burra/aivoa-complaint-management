
const ChatMessage = ({ role, content }) => {
  return (
    <div className={`message-bubble message-${role}`}>
      {content}
    </div>
  );
};
export default ChatMessage;
